from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, InputMediaPhoto, Message

from bot import texts
from bot.db.models import Profile, User
from bot.keyboards.common import decisions, home
from bot.services.store import Store
from bot.services.telegram import caption, notify_decision, safe_call, target_id
from bot.services.validation import RuleError

router = Router(name="discovery")
MESSAGE_ID_KEY = "discovery_message_id"
PHOTO_ID_KEY = "discovery_photo_file_id"


def _edit_error(error: TelegramBadRequest) -> str:
    return error.message.casefold().replace("’", "'")


def _message_cannot_be_edited(error: TelegramBadRequest) -> bool:
    message = _edit_error(error)
    return any(
        reason in message
        for reason in (
            "message to edit not found",
            "message can't be edited",
            "message can not be edited",
            "message_id_invalid",
            "there is no media in the message to edit",
        )
    )


async def _send_profile(
    message: Message,
    state: FSMContext,
    photo_file_id: str,
    text: str,
    reply_markup: InlineKeyboardMarkup,
) -> None:
    sent = await message.answer_photo(photo_file_id, caption=text, reply_markup=reply_markup)
    await state.update_data(
        {MESSAGE_ID_KEY: sent.message_id, PHOTO_ID_KEY: photo_file_id}
    )


async def _show_profile(
    message: Message, state: FSMContext, profile: Profile, incoming: bool
) -> None:
    data = await state.get_data()
    message_id = data.get(MESSAGE_ID_KEY)
    previous_photo = data.get(PHOTO_ID_KEY)
    text = caption(profile)
    reply_markup = decisions(profile.user_id, incoming)

    if not isinstance(message_id, int) or isinstance(message_id, bool) or message_id <= 0:
        await _send_profile(message, state, profile.photo_file_id, text, reply_markup)
        return

    bot = message.bot
    if bot is None:
        await _send_profile(message, state, profile.photo_file_id, text, reply_markup)
        return

    try:
        if previous_photo == profile.photo_file_id:
            await bot.edit_message_caption(
                chat_id=message.chat.id,
                message_id=message_id,
                caption=text,
                reply_markup=reply_markup,
            )
        else:
            await bot.edit_message_media(
                chat_id=message.chat.id,
                message_id=message_id,
                media=InputMediaPhoto(media=profile.photo_file_id, caption=text),
                reply_markup=reply_markup,
            )
    except TelegramBadRequest as exc:
        if "message is not modified" in _edit_error(exc):
            await state.update_data({PHOTO_ID_KEY: profile.photo_file_id})
            return
        if not _message_cannot_be_edited(exc):
            raise
        await _send_profile(message, state, profile.photo_file_id, text, reply_markup)
        return

    await state.update_data({PHOTO_ID_KEY: profile.photo_file_id})


async def show_next(
    message: Message, state: FSMContext, store: Store, user: User, incoming: bool = False
) -> bool:
    profile = await store.next_profile(user.id, incoming)
    if profile is None:
        await message.answer(texts.NO_LIKES if incoming else texts.NO_PROFILES, reply_markup=home())
        return False
    await _show_profile(message, state, profile, incoming)
    return True


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[0]))
@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[2]))
async def discover(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    await show_next(message, state, store, user, message.text in texts.MENU_LABEL_ALIASES[2])


@router.callback_query(F.data == "incoming")
async def incoming(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    if isinstance(callback.message, Message):
        await show_next(callback.message, state, store, user, True)


@router.callback_query(F.data.startswith("react:"))
async def react(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    if not isinstance(callback.message, Message) or callback.bot is None or callback.data is None:
        return
    message = callback.message
    bot = callback.bot
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[3] not in {"i", "d"}:
        raise RuleError("Кнопка устарела или недействительна.")
    target, kind, source = target_id(parts[1]), parts[2], parts[3]
    result = await store.decide(user.id, target, kind)
    if not result.created:
        await callback.message.answer("Твоё решение по этой анкете уже сохранено.")
        return
    await notify_decision(callback.bot, store, user.telegram_id, result, kind)
    if not await show_next(message, state, store, user, source == "i"):
        await safe_call(
            store,
            user.telegram_id,
            lambda: bot.edit_message_reply_markup(
                chat_id=message.chat.id,
                message_id=message.message_id,
                reply_markup=None,
            ),
        )
