from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import inline, match_actions
from bot.services.store import Store
from bot.services.telegram import caption, contact_url, target_id
from bot.services.validation import RuleError

router = Router(name="matches")


async def show_matches(message: Message, store: Store, user: User, page: int = 0) -> None:
    entries = await store.match_page(user.id, page)
    rows = [
        ((f"{profile.name}, {profile.age}", f"match:{match.id}"),) for match, profile in entries
    ]
    navigation = []
    if page:
        navigation.append(("← Назад", f"matches:{page - 1}"))
    if len(entries) == 5:
        navigation.append(("Далее →", f"matches:{page + 1}"))
    if navigation:
        rows.append(tuple(navigation))
    rows.append((("🏠 В меню", "home"),))
    await message.answer(
        (f"<b>✨ Взаимные симпатии</b>\nСтраница {page + 1}" if entries else texts.NO_MATCHES),
        reply_markup=inline(*rows),
    )


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[3]))
async def match_menu(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    await show_matches(message, store, user)


@router.callback_query(F.data.startswith("matches:"))
async def match_page(callback: CallbackQuery, store: Store, user: User) -> None:
    value = callback.data.split(":", 1)[1]
    page = 0 if value == "0" else target_id(value)
    await show_matches(callback.message, store, user, page)


@router.callback_query(F.data.startswith("match:"))
async def match_open(callback: CallbackQuery, store: Store, user: User) -> None:
    match_id = target_id(callback.data.split(":", 1)[1])
    target = await store.match_target(user.id, match_id)
    profile = await store.profile(target.id)
    if not profile:
        raise RuleError("Анкета удалена.")
    await callback.message.answer_photo(
        profile.photo_file_id,
        caption=caption(profile),
        reply_markup=match_actions(match_id, target.id),
    )


@router.callback_query(F.data.startswith("contact:"))
async def contact(callback: CallbackQuery, store: Store, user: User) -> None:
    match_id = target_id(callback.data.split(":", 1)[1])
    url = await contact_url(callback.bot, store, user.id, match_id)
    if url:
        await callback.message.answer(
            f"<b>💬 Контакт открыт</b>\n{escape(url)}\n\n"
            "Общение продолжится в личном чате Telegram."
        )
    else:
        await callback.message.answer(
            "<b>Контакт пока недоступен</b>\n"
            "Попроси пользователя добавить Telegram username и попробуй ещё раз позже.",
            reply_markup=inline(
                (("Попробовать снова", f"contact:{match_id}"),), (("🏠 В меню", "home"),)
            ),
        )
