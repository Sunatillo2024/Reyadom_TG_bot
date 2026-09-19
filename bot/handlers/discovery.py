from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import decisions, home
from bot.services.store import Store
from bot.services.telegram import caption, navigate, notify_decision, target_id
from bot.services.validation import RuleError

router = Router(name="discovery")


async def show_next(
    event: Message | CallbackQuery, store: Store, user: User, incoming: bool = False
) -> None:
    profile = await store.next_profile(user.id, incoming)
    if profile is None:
        await navigate(event, texts.NO_LIKES if incoming else texts.NO_PROFILES, home())
        return
    await navigate(
        event,
        caption(profile),
        decisions(profile.user_id, incoming),
        photo=profile.photo_file_id,
    )


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[0]))
@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[2]))
@router.callback_query(F.data == "discover")
async def discover(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()
    incoming = isinstance(event, Message) and event.text in texts.MENU_LABEL_ALIASES[2]
    await show_next(event, store, user, incoming)


@router.callback_query(F.data == "incoming")
async def incoming(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    await show_next(callback, store, user, True)


@router.callback_query(F.data.startswith("react:"))
async def react(callback: CallbackQuery, store: Store, user: User) -> None:
    parts = callback.data.split(":")
    if len(parts) != 4 or parts[3] not in {"i", "d"}:
        raise RuleError("Кнопка устарела или недействительна.")
    target, kind, source = target_id(parts[1]), parts[2], parts[3]
    result = await store.decide(user.id, target, kind)
    if result.created:
        await notify_decision(callback.bot, store, user.telegram_id, result, kind)
    await show_next(callback, store, user, source == "i")
