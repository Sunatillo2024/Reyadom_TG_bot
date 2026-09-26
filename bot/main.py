import asyncio
import logging
import sys
from collections.abc import AsyncGenerator, Awaitable, Callable
from contextlib import suppress
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import (
    TelegramConflictError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
    TelegramUnauthorizedError,
)
from aiogram.fsm.storage.base import BaseEventIsolation, BaseStorage, DefaultKeyBuilder
from aiogram.fsm.storage.redis import RedisEventIsolation, RedisStorage
from aiogram.methods import GetUpdates
from aiogram.types import BotCommand, CallbackQuery, ChatMemberUpdated, ErrorEvent, Message, Update
from aiogram.utils.backoff import BackoffConfig
from aiogram.utils.token import TokenValidationError, validate_token
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError
from redis.exceptions import RedisError
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from bot.config import Settings
from bot.db.database import Database
from bot.handlers import (
    admin,
    discovery,
    matches,
    moderation,
    payments,
    premium,
    profile,
    registration,
    start,
)
from bot.i18n import DEFAULT_LANGUAGE, LANGUAGES, tr
from bot.middlewares.access import AccessMiddleware
from bot.services.payments import PaymentService
from bot.services.store import Store
from bot.services.welcome_trial import deliver_trial_notifications

logger = logging.getLogger(__name__)
PROJECT_ROOT = Path(__file__).resolve().parents[1]


async def payment_notification_loop(bot: Bot, store: Store) -> None:
    """Deliver persisted payment and welcome-trial notifications."""
    service = PaymentService(store)
    while True:
        try:
            for order in await service.pending_notifications():
                await payments.deliver_payment_notification(bot, service, order.id)
            await deliver_trial_notifications(bot, store)
        except Exception as exc:
            logger.warning("Ошибка повтора платёжных уведомлений: %s", type(exc).__name__)
        await asyncio.sleep(60)


def migration_head() -> str:
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    head = ScriptDirectory.from_config(config).get_current_head()
    if head is None:
        raise RuntimeError("Alembic не содержит миграций")
    return head


async def retry_telegram(
    call: Callable[[], Awaitable[object]], *, attempts: int = 5, base_delay: float = 1.0
) -> None:
    """Run a startup Telegram call, retrying transient network failures.

    A container may start before the network route to api.telegram.org is ready.
    Without retries the process crashes and relies on a Docker restart to get a
    second chance; retrying here makes startup deterministic.
    """
    for attempt in range(1, attempts + 1):
        try:
            await call()
            return
        except TelegramRetryAfter as exc:
            delay = float(exc.retry_after)
        except (TelegramNetworkError, TelegramServerError):
            delay = base_delay * (2 ** (attempt - 1))
        if attempt >= attempts:
            raise
        logger.warning(
            "Telegram API vaqtincha javob bermadi; urinish %s/%s, %s s dan keyin qayta",
            attempt,
            attempts,
            delay,
        )
        await asyncio.sleep(delay)


class PollingDispatcher(Dispatcher):
    @classmethod
    async def _listen_updates(
        cls,
        bot: Bot,
        polling_timeout: int = 30,
        backoff_config: BackoffConfig | None = None,
        allowed_updates: list[str] | None = None,
    ) -> AsyncGenerator[Update, None]:
        """Bound reconnect attempts; conflict/auth errors immediately reach main()."""
        request = GetUpdates(timeout=polling_timeout, allowed_updates=allowed_updates)
        failures = 0
        while True:
            try:
                updates = await bot(request, request_timeout=polling_timeout + 10)
            except (TelegramNetworkError, TelegramServerError, TelegramRetryAfter) as exc:
                failures += 1
                if failures >= 5:
                    raise
                delay = exc.retry_after if isinstance(exc, TelegramRetryAfter) else 2**failures
                if delay > 60:
                    raise
                logger.warning(
                    "Соединение опроса прервано; попытка %s/5, задержка %s с", failures, delay
                )
                await asyncio.sleep(delay)
                continue
            if failures:
                logger.info("Соединение опроса восстановлено")
            failures = 0
            for update in updates:
                yield update
                request.offset = update.update_id + 1


def create_redis_storage(settings: Settings) -> RedisStorage:
    """Create the single Redis client used for FSM data and update locks."""
    return RedisStorage.from_url(
        settings.redis_url,
        key_builder=DefaultKeyBuilder(prefix="fsm", with_bot_id=True),
        state_ttl=settings.fsm_state_ttl,
        data_ttl=settings.fsm_data_ttl,
    )


async def verify_redis_connection(storage: RedisStorage) -> bool:
    """Ping Redis before accepting updates without exposing connection secrets."""
    try:
        if await storage.redis.ping():
            logger.info("Redis FSM storage ulandi")
            return True
    except RedisError as exc:
        logger.error(
            "Redis ulanib bo'lmadi; bot ishga tushmaydi. "
            "REDIS_URL va Redis servisni tekshiring (%s).",
            type(exc).__name__,
        )
        return False
    logger.error("Redis PING kutilgan PONG javobini bermadi; bot ishga tushmaydi")
    return False


def create_dispatcher(
    store: Store, storage: BaseStorage, events_isolation: BaseEventIsolation
) -> Dispatcher:
    dispatcher = PollingDispatcher(storage=storage, events_isolation=events_isolation)
    dispatcher["store"] = store
    access = AccessMiddleware(store)
    dispatcher.message.outer_middleware(access)
    dispatcher.callback_query.outer_middleware(access)
    # Commands precede forms so /cancel, /privacy and /delete work at every step.
    dispatcher.include_routers(
        payments.router,
        start.router,
        admin.router,
        premium.router,
        profile.router,
        discovery.router,
        matches.router,
        moderation.router,
        registration.router,
    )
    fallback = Router(name="fallback")

    @fallback.callback_query()
    async def stale(callback: CallbackQuery) -> None:
        text = tr("stale_button")
        if isinstance(callback.message, Message):
            await callback.message.answer(text)
        else:
            await callback.answer(text, show_alert=True)

    @fallback.message()
    async def unknown(message: Message) -> None:
        await message.answer(tr("unknown_message"))

    @fallback.my_chat_member()
    async def membership(event: ChatMemberUpdated) -> None:
        if event.chat.type == "private" and event.new_chat_member.status == "kicked":
            await store.hide_telegram(event.chat.id)

    @fallback.errors()
    async def unexpected(event: ErrorEvent) -> bool:
        logger.error("Ошибка обработки обновления: %s", type(event.exception).__name__)
        return True

    dispatcher.include_router(fallback)
    return dispatcher


def bot_commands(language: str | None = None) -> list[BotCommand]:
    """Command menu localized through the lexicon for one Telegram client language."""
    return [
        BotCommand(command="start", description=tr("cmd_start", language)),
        BotCommand(command="help", description=tr("cmd_help", language)),
        BotCommand(command="privacy", description=tr("cmd_privacy", language)),
        BotCommand(command="terms", description=tr("cmd_terms", language)),
        BotCommand(command="paysupport", description=tr("cmd_paysupport", language)),
        BotCommand(command="cancel", description=tr("cmd_cancel", language)),
        BotCommand(command="id", description=tr("cmd_id", language)),
        BotCommand(command="delete", description=tr("cmd_delete", language)),
    ]


async def run(settings: Settings) -> int:
    token = settings.bot_token.get_secret_value().strip()
    try:
        validate_token(token)
    except TokenValidationError:
        print(
            "BOT_TOKEN пуст или имеет неверный формат. Укажите токен BotFather в файле .env.",
            file=sys.stderr,
        )
        return 2
    db = Database(settings.database_url)
    store = Store(
        db,
        settings.admin_ids,
        stars_sales_enabled=settings.stars_sales_enabled,
        welcome_trial_enabled=settings.welcome_trial_enabled,
        welcome_trial_days=settings.welcome_trial_days,
    )
    bot = Bot(token, default=DefaultBotProperties(parse_mode="HTML"))
    storage = create_redis_storage(settings)
    dispatcher = create_dispatcher(
        store,
        storage,
        RedisEventIsolation(redis=storage.redis, key_builder=storage.key_builder),
    )
    notification_task: asyncio.Task[None] | None = None
    try:
        try:
            async with db.engine.connect() as connection:
                version = await connection.scalar(text("SELECT version_num FROM alembic_version"))
                if version != migration_head():
                    raise RuntimeError("migration")
        except (SQLAlchemyError, RuntimeError):
            print("База данных не готова. Сначала выполните alembic upgrade head.", file=sys.stderr)
            return 2
        if not await verify_redis_connection(storage):
            return 2
        # Command menu follows the Telegram client language; default covers the rest.
        await retry_telegram(lambda: bot.set_my_commands(bot_commands(DEFAULT_LANGUAGE)))
        for language in LANGUAGES:
            if language != DEFAULT_LANGUAGE:
                await retry_telegram(
                    lambda lang=language: bot.set_my_commands(
                        bot_commands(lang), language_code=lang
                    )
                )
        # Keep pending updates. Never drop registration decisions on startup.
        await retry_telegram(lambda: bot.delete_webhook(drop_pending_updates=False))
        logger.info("Bot ishga tushdi: Telegram bilan aloqa o'rnatildi, polling boshlanadi")
        notification_task = asyncio.create_task(payment_notification_loop(bot, store))
        await dispatcher.start_polling(
            bot,
            close_bot_session=False,
            handle_as_tasks=False,
            allowed_updates=dispatcher.resolve_used_update_types(),
        )
    except TelegramUnauthorizedError:
        logger.error("Telegram отклонил BOT_TOKEN")
        return 2
    except TelegramConflictError:
        logger.error("С этим токеном уже работает другой процесс опроса; остановите его")
        return 2
    finally:
        if notification_task:
            notification_task.cancel()
            with suppress(asyncio.CancelledError):
                await notification_task
        await dispatcher.fsm.close()
        await bot.session.close()
        await db.close()
    return 0


def main() -> None:
    try:
        settings = Settings()  # type: ignore[call-arg]
    except ValidationError as exc:
        fields = ", ".join(".".join(map(str, error["loc"])) for error in exc.errors())
        print(f"Неверные настройки .env: {fields}. Проверьте .env.example.", file=sys.stderr)
        raise SystemExit(2) from None
    logging.basicConfig(
        level=settings.log_level, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    # HTTP/library debug logs can include request contents. Keep them quiet even in DEBUG.
    for name in ("aiohttp", "aiogram", "sqlalchemy", "asyncpg"):
        logging.getLogger(name).setLevel(logging.WARNING)
    try:
        code = asyncio.run(run(settings))
    except KeyboardInterrupt:
        code = 0
    except Exception as exc:
        logger.error("Ошибка запуска: %s", type(exc).__name__)
        code = 1
    raise SystemExit(code)


if __name__ == "__main__":
    main()
