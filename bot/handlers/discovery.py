from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import decisions, home
from bot.services.store import Store
from bot.services.telegram import caption, notify_decision, safe_call, target_id
from bot.services.validation import RuleError

router = Router(name="discovery")


async def show_next(message: Message, store: Store, user: User, incoming: bool = False) -> None:
    profile = await store.next_profile(user.id, incoming)
    if profile is None:
        await message.answer(texts.NO_LIKES if incoming else texts.NO_PROFILES, reply_markup=home())
        return
    await message.answer_photo(
        profile.photo_file_id,
        caption=caption(profile),
        reply_markup=decisions(profile.user_id, incoming),
    )


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[0]))
@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[2]))
async def discover(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    await show_next(message, store, user, message.text in texts.MENU_LABEL_ALIASES[2])


@router.callback_query(F.data == "incoming")
async def incoming(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    await show_next(callback.message, store, user, True)


@router.callback_query(F.data.startswith("react:"))
async def react(callback: CallbackQuery, store: Store, user: User) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[3] not in {"i", "d"}:
        raise RuleError("Кнопка устарела или недействительна.")
    target, kind, source = target_id(parts[1]), parts[2], parts[3]
    result = await store.decide(user.id, target, kind)
    await safe_call(
        store, user.telegram_id, lambda: callback.message.edit_reply_markup(reply_markup=None)
    )
    if not result.created:
        await callback.message.answer("Твоё решение по этой анкете уже сохранено.")
        return
    await notify_decision(callback.bot, store, user.telegram_id, result, kind)
    await show_next(callback.message, store, user, source == "i")
