from html import escape

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.i18n import localized_labels, tr
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
        navigation.append((tr("matches_prev"), f"matches:{page - 1}"))
    if len(entries) == 5:
        navigation.append((tr("matches_next"), f"matches:{page + 1}"))
    if navigation:
        rows.append(tuple(navigation))
    rows.append(((tr("back_menu"), "home"),))
    await message.answer(
        (tr("matches_title_page", page=page + 1) if entries else tr("no_matches")),
        reply_markup=inline(*rows),
    )


@router.message(F.text.in_(localized_labels("menu_matches")))
async def match_menu(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    await show_matches(message, store, user)


@router.callback_query(F.data.startswith("matches:"))
async def match_page(callback: CallbackQuery, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    value = callback.data.split(":", 1)[1]
    page = 0 if value == "0" else target_id(value)
    await show_matches(callback.message, store, user, page)


@router.callback_query(F.data.startswith("match:"))
async def match_open(callback: CallbackQuery, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    match_id = target_id(callback.data.split(":", 1)[1])
    target = await store.match_target(user.id, match_id)
    profile = await store.profile(target.id)
    if not profile:
        raise RuleError(tr("err_profile_deleted"))
    await callback.message.answer_photo(
        profile.photo_file_id,
        caption=caption(profile),
        reply_markup=match_actions(match_id, target.id),
    )


@router.callback_query(F.data.startswith("contact:"))
async def contact(callback: CallbackQuery, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message) or callback.bot is None:
        return
    match_id = target_id(callback.data.split(":", 1)[1])
    url = await contact_url(callback.bot, store, user.id, match_id)
    if url:
        await callback.message.answer(tr("contact_opened", url=escape(url)))
    else:
        await callback.message.answer(
            tr("contact_unavailable"),
            reply_markup=inline(
                ((tr("contact_retry"), f"contact:{match_id}"),),
                ((tr("back_menu"), "home"),),
            ),
        )
