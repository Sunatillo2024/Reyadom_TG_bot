import asyncio
import logging
import sys
from collections.abc import AsyncGenerator
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
from aiogram.fsm.storage.memory import MemoryStorage, SimpleEventIsolation
from aiogram.methods import GetUpdates
from aiogram.types import BotCommand, CallbackQuery, ChatMemberUpdated, ErrorEvent, Message, Update
from aiogram.utils.backoff import BackoffConfig
from aiogram.utils.token import TokenValidationError, validate_token
from alembic.config import Config
from alembic.script import ScriptDirectory
from pydantic import ValidationError
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
            failures = 0
            for update in updates:
                yield update
                request.offset = update.update_id + 1


def create_dispatcher(store: Store) -> Dispatcher:
    dispatcher = PollingDispatcher(storage=MemoryStorage(), events_isolation=SimpleEventIsolation())
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
        text = "Кнопка устарела или недействительна. Продолжи с помощью /start."
        if isinstance(callback.message, Message):
            await callback.message.answer(text)
        else:
            await callback.answer(text, show_alert=True)

    @fallback.message()
    async def unknown(message: Message) -> None:
        await message.answer("Выбери пункт меню или отправь /start. /cancel — отмена.")

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
    dispatcher = create_dispatcher(store)
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
        await bot.set_my_commands(
            [
                BotCommand(command="start", description="Меню и регистрация"),
                BotCommand(command="help", description="Помощь"),
                BotCommand(command="privacy", description="Конфиденциальность"),
                BotCommand(command="terms", description="Условия покупки Premium"),
                BotCommand(command="paysupport", description="Поддержка по платежам"),
                BotCommand(command="cancel", description="Отменить действие"),
                BotCommand(command="id", description="Мой Telegram ID"),
                BotCommand(command="delete", description="Удалить анкету"),
            ]
        )
        # Keep pending updates. Never drop registration decisions on startup.
        await bot.delete_webhook(drop_pending_updates=False)
        logger.info("Запускается опрос Telegram для бота знакомств")
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
