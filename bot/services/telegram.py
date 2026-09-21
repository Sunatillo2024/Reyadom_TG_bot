import logging
import re
from collections.abc import Awaitable, Callable
from html import escape
from typing import Any

from aiogram import Bot
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)

from bot.db.models import Profile
from bot.keyboards.common import inline
from bot.services.store import Decision, Store
from bot.services.validation import RuleError

logger = logging.getLogger(__name__)


def caption(profile: Profile, show_badge: bool = False) -> str:
    # Visible text stays below the caption limit; escaping prevents HTML injection.
    distance = getattr(profile, "distance_km", None)
    location = f"📍 {distance:g} км от тебя" if distance is not None else "📍 Геолокация"
    if profile.latitude is None or profile.longitude is None:
        location = f"📍 {escape(profile.city)}"
    badge = " 💎" if show_badge else ""
    parts = [f"<b>{escape(profile.name)}, {profile.age}</b>{badge}\n{location}"]
    if profile.bio:
        parts.append(escape(profile.bio))
    return "\n\n".join(parts)


async def safe_call(store: Store, telegram_id: int, call: Callable[[], Awaitable[Any]]) -> Any:
    try:
        return await call()
    except TelegramForbiddenError:
        await store.hide_telegram(telegram_id)
        logger.info("Получатель заблокировал бота в Telegram; анкета скрыта")
    except TelegramRetryAfter as exc:
        logger.warning(
            "Ограничение частоты Telegram: %s с; повторной отправки не было",
            exc.retry_after,
        )
    except TelegramBadRequest as exc:
        logger.warning("Telegram отклонил запрос; повторной отправки не было: %s", exc.message)
    except (TelegramNetworkError, TelegramServerError, TimeoutError, OSError):
        logger.warning("Временная ошибка связи с Telegram; повторной отправки не было")
    return None


async def notify_decision(
    bot: Bot, store: Store, actor_telegram_id: int, result: Decision, kind: str
) -> None:
    if not result.created or kind != "like":
        return
    if result.match_id:
        keyboard = inline((("💜 Посмотреть анкету", f"match:{result.match_id}", "primary"),))
        recipients = [actor_telegram_id]
        if result.recipient_telegram_id is not None:
            recipients.append(result.recipient_telegram_id)
        for recipient in recipients:
            await safe_call(
                store,
                recipient,
                lambda recipient=recipient: bot.send_message(
                    recipient,
                    "<b>У вас взаимная симпатия! 💜</b>\n\n"
                    "Открой контакт, чтобы познакомиться поближе.",
                    reply_markup=keyboard,
                ),
            )
    else:
        recipient = result.recipient_telegram_id
        if recipient is None:
            return
        await safe_call(
            store,
            recipient,
            lambda: bot.send_message(
                recipient,
                "<b>💌 Кому-то понравилась твоя анкета</b>\n\n"
                "Посмотри входящие лайки — возможно, симпатия взаимна.",
                reply_markup=inline((("💌 Посмотреть лайки", "incoming", "primary"),)),
            ),
        )


async def contact_url(bot: Bot, store: Store, actor: int, match_id: int) -> str | None:
    target = await store.match_target(actor, match_id)
    chat = await safe_call(store, target.telegram_id, lambda: bot.get_chat(target.telegram_id))
    if chat is None:
        return None
    if chat.id != target.telegram_id or chat.type != "private":
        return None
    username = chat.username
    await store.sync_user(target.telegram_id, username)
    # Recheck after the API await: a concurrent ban/block/deletion must win.
    await store.match_target(actor, match_id)
    if not username or not re.fullmatch(r"[A-Za-z0-9_]{1,64}", username):
        return None
    return f"https://t.me/{username}"


def target_id(value: str) -> int:
    if not value.isascii() or not value.isdecimal() or not 0 < int(value) <= 2**63 - 1:
        raise RuleError("Кнопка устарела или недействительна.")
    return int(value)
