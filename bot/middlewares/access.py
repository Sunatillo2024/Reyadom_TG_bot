import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.types import CallbackQuery, Message, TelegramObject

from bot import texts
from bot.keyboards.common import inline
from bot.services.store import Store
from bot.services.telegram import safe_call
from bot.services.validation import RuleError
from bot.services.welcome_trial import deliver_trial_notifications

logger = logging.getLogger(__name__)


class AccessMiddleware(BaseMiddleware):
    def __init__(self, store: Store) -> None:
        self.store = store
        self.last_decision: dict[int, float] = {}

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if not isinstance(event, (Message, CallbackQuery)):
            return None
        callback = isinstance(event, CallbackQuery)
        # Answer even malformed, banned and group callbacks before DB work.
        if callback:
            await safe_call(self.store, event.from_user.id, lambda: event.answer())
        message = event.message if callback else event
        if not message or message.chat.type != "private" or not event.from_user:
            return None
        telegram_id = event.from_user.id
        if message.chat.id != telegram_id:
            return None
        try:
            sync_result = await self.store.sync_user_with_status(
                telegram_id, event.from_user.username
            )
            user = sync_result.user
            data.update(store=self.store, user=user)
            await deliver_trial_notifications(data["bot"], self.store, user_id=user.id)
            command = (event.data or "") if callback else (event.text or "").split(" ")[0]
            allowed = {
                "/start",
                "/help",
                "/privacy",
                "/id",
                "/cancel",
                "/delete",
                "/terms",
                "/paysupport",
                "❓",
                "❔",
                "👤",
                "delete",
                "delete:yes",
                "home",
                "home:cancel",
            }
            payment_event = isinstance(message, Message) and bool(
                message.successful_payment or message.refunded_payment
            )
            if user.is_banned and command not in allowed and not payment_event:
                raise RuleError("Твой доступ ограничен. Доступны /help, /privacy и /delete.")
            if callback and command.startswith("react:"):
                now = time.monotonic()
                if now - self.last_decision.get(telegram_id, 0) < 1:
                    raise RuleError("Подожди секунду и нажми снова.")
                self.last_decision[telegram_id] = now
                if len(self.last_decision) > 10_000:
                    self.last_decision = {
                        key: stamp for key, stamp in self.last_decision.items() if now - stamp < 60
                    }
            return await handler(event, data)
        except RuleError as exc:
            error_text = str(exc)
            await safe_call(
                self.store,
                telegram_id,
                lambda: data["bot"].send_message(
                    telegram_id,
                    error_text,
                    parse_mode=None,
                    reply_markup=inline((("🏠 В меню", "home"),)),
                ),
            )
        except TelegramForbiddenError:
            await self.store.hide_telegram(telegram_id)
            logger.info("Бот заблокирован; анкета скрыта")
        except TelegramRetryAfter as exc:
            logger.warning("Ограничение частоты Telegram: %s с", exc.retry_after)
        except TelegramBadRequest as exc:
            logger.warning("Telegram не принял сообщение или фото: %s", exc.message)
            await safe_call(
                self.store,
                telegram_id,
                lambda: data["bot"].send_message(
                    telegram_id,
                    "Не получилось отправить сообщение или фото. Попробуй ещё раз. "
                    "Если фото устарело, обнови его в разделе «Моя анкета».",
                ),
            )
        except (TelegramNetworkError, TelegramServerError, TimeoutError, OSError):
            logger.warning("Временная ошибка связи с Telegram")
            await safe_call(
                self.store,
                telegram_id,
                lambda: data["bot"].send_message(telegram_id, texts.TEMPORARY_ERROR),
            )
        except Exception:
            logger.exception("Непредвиденная ошибка при обработке обновления")
            await safe_call(
                self.store,
                telegram_id,
                lambda: data["bot"].send_message(telegram_id, texts.TEMPORARY_ERROR),
            )
        return None
