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
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    Message,
)

from bot.db.models import Profile
from bot.keyboards.common import inline, remove_keyboard
from bot.services.store import Decision, Store
from bot.services.validation import RuleError

logger = logging.getLogger(__name__)

_NOT_EDITED = "message is not modified"
_EDIT_FALLBACK_ERRORS = (
    "message to edit not found",
    "message can't be edited",
    "message identifier is not specified",
    "message_id_invalid",
)
_INVALID_MEDIA_ERRORS = (
    "wrong file identifier",
    "failed to get http url content",
    "can't use file of type",
)


def _error_contains(exc: TelegramBadRequest, phrases: tuple[str, ...]) -> bool:
    return any(phrase in exc.message.lower() for phrase in phrases)


async def send_navigation(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    photo: str | None = None,
) -> Message:
    """Create the single navigation message after a user text/command.

    The first request removes any legacy reply keyboard. Adding the inline markup
    immediately afterwards does not create another visible chat message.
    """
    if photo:
        try:
            sent = await message.answer_photo(
                photo, caption=text, reply_markup=remove_keyboard()
            )
        except TelegramBadRequest as exc:
            if not _error_contains(exc, _INVALID_MEDIA_ERRORS):
                raise
            sent = await message.answer(text, reply_markup=remove_keyboard())
    else:
        sent = await message.answer(text, reply_markup=remove_keyboard())
    result = await sent.edit_reply_markup(reply_markup=reply_markup)
    return result if isinstance(result, Message) else sent


async def update_navigation(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    photo: str | None = None,
) -> Message:
    """Update a navigation message and create a replacement only when necessary.

    Telegram cannot turn a plain text message into a media message. That case, and
    messages that were deleted or can no longer be edited, use one controlled
    replacement. Unexpected API errors are deliberately re-raised.
    """
    if photo and not message.photo:
        return await _replace_navigation(message, text, reply_markup, photo=photo)
    try:
        if photo:
            result = await message.edit_media(
                InputMediaPhoto(media=photo, caption=text), reply_markup=reply_markup
            )
        elif message.photo:
            result = await message.edit_caption(caption=text, reply_markup=reply_markup)
        else:
            result = await message.edit_text(text, reply_markup=reply_markup)
    except TelegramBadRequest as exc:
        if _error_contains(exc, (_NOT_EDITED,)):
            return message
        if photo and _error_contains(exc, _INVALID_MEDIA_ERRORS):
            return await _replace_navigation(message, text, reply_markup, photo=None)
        if _error_contains(exc, _EDIT_FALLBACK_ERRORS):
            return await _replace_navigation(message, text, reply_markup, photo=photo)
        raise
    return result if isinstance(result, Message) else message


async def _replace_navigation(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    photo: str | None,
) -> Message:
    # Disable the obsolete menu when it still exists. Only known edit failures are
    # ignored; an unrelated Telegram error must remain visible to middleware/logs.
    try:
        await message.edit_reply_markup(reply_markup=None)
    except TelegramBadRequest as exc:
        if not (
            _error_contains(exc, (_NOT_EDITED,))
            or _error_contains(exc, _EDIT_FALLBACK_ERRORS)
        ):
            raise
    return await send_navigation(message, text, reply_markup, photo=photo)


async def navigate(
    event: Message | CallbackQuery,
    text: str,
    reply_markup: InlineKeyboardMarkup,
    *,
    photo: str | None = None,
) -> Message:
    """Render navigation from either a user message or an inline callback."""
    if isinstance(event, CallbackQuery):
        if not isinstance(event.message, Message):
            if photo:
                return await event.bot.send_photo(
                    event.from_user.id, photo, caption=text, reply_markup=reply_markup
                )
            return await event.bot.send_message(
                event.from_user.id, text, reply_markup=reply_markup
            )
        return await update_navigation(event.message, text, reply_markup, photo=photo)
    return await send_navigation(event, text, reply_markup, photo=photo)


def caption(profile: Profile) -> str:
    # Visible text stays below the caption limit; escaping prevents HTML injection.
    distance = getattr(profile, "distance_km", None)
    location = f"📍 {distance:g} км от тебя" if distance is not None else "📍 Геолокация"
    if profile.latitude is None or profile.longitude is None:
        location = f"📍 {escape(profile.city)}"
    parts = [f"<b>{escape(profile.name)}, {profile.age}</b>\n{location}"]
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
        for recipient in (actor_telegram_id, result.recipient_telegram_id):
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
