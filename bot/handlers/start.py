from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.handlers.registration import continue_registration
from bot.i18n import language_from_code, localized_labels, tr
from bot.keyboards.common import inline, language_continue, language_selection, menu
from bot.services.store import Store
from bot.states import Registration

router = Router(name="start")


async def show_home(
    message: Message,
    state: FSMContext,
    store: Store,
    user: User,
    *,
    has_anketa: bool | None = None,
) -> None:
    """Route by the one-time consent flag, then by anketa existence.

    The 18+/consent screens are asked exactly once per Telegram account: they
    appear only while the user row has no recorded consent. Once the user has
    accepted (the flag lives on the user row, not the profile), deleting the
    anketa never brings the screens back — the flow resumes at anketa filling.
    """
    await state.clear()
    if user.is_banned:
        await message.answer(
            tr("access_restricted"),
            reply_markup=menu(),
        )
        return
    if has_anketa is None:
        has_anketa = await store.profile_exists(user.telegram_id)
    if has_anketa:
        # Existing anketa: straight to the main menu, no 18+/consent repeat.
        await message.answer(tr("home"), reply_markup=menu())
        return
    if user.consent_at is not None:
        # Consent already accepted once: skip straight into anketa creation.
        await continue_registration(message, state, user)
        return
    await state.set_state(Registration.adult)
    await message.answer(
        tr("intro"),
        reply_markup=inline(
            ((tr("reg_adult_button"), "reg:adult", "primary"),),
            ((tr("delete_cancel"), "home:cancel"),),
        ),
    )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    # 1) The gate is the user row itself: recorded consent or an existing anketa.
    if user.consent_at is not None or await store.profile_exists(user.telegram_id):
        # 2-3) Returning user: straight to the menu or anketa continuation —
        # the 18+/consent screens never reappear.
        await show_home(message, state, store, user)
        return
    # 4) Brand-new account: pick the language first (only once), then age/consent.
    if user.language is None:
        await message.answer(
            tr("welcome", language_from_code(message.from_user.language_code)),
            reply_markup=language_selection(),
        )
    else:
        await show_home(message, state, store, user)


@router.callback_query(F.data == "settings:language")
async def change_language(callback: CallbackQuery) -> None:
    if isinstance(callback.message, Message):
        await callback.message.answer(tr("welcome"), reply_markup=language_selection())


@router.callback_query(F.data.startswith("lang:"))
async def select_language(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    if callback.data is None or callback.message is None:
        return
    # set_language validates the raw value so an unknown code raises a localized error.
    language = callback.data.split(":", 1)[1]
    await store.set_language(user.id, language)
    await state.clear()
    await callback.message.answer(
        tr("language_selected", language),
        reply_markup=language_continue(tr("continue", language)),
    )


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await show_home(callback.message, state, store, user)


@router.message(Command("cancel"))
@router.callback_query(F.data == "home:cancel")
async def cancel(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    message = event.message if isinstance(event, CallbackQuery) else event
    if message is None or not isinstance(message, Message):
        return
    await message.answer(
        tr("cancel_done"), reply_markup=menu()
    )


@router.message(Command("help"))
@router.message(F.text.in_(localized_labels("menu_help")))
async def help_message(message: Message) -> None:
    await message.answer(tr("help"))


@router.message(Command("privacy"))
async def privacy(message: Message) -> None:
    await message.answer(tr("privacy") + tr("delete_notice"))


@router.message(Command("id"))
async def own_id(message: Message) -> None:
    if message.from_user is None:
        return
    await message.answer(tr("own_id", telegram_id=message.from_user.id))


@router.message(Command("delete"))
@router.callback_query(F.data == "delete")
async def delete_prompt(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(delete_requested=True)
    message = event.message if isinstance(event, CallbackQuery) else event
    if message is None or not isinstance(message, Message):
        return
    await message.answer(
        tr("delete_notice"),
        reply_markup=inline(
            ((tr("delete_confirm"), "delete:yes", "danger"),),
            ((tr("delete_cancel"), "home:cancel"),),
        ),
    )


@router.callback_query(F.data == "delete:yes")
async def delete_confirm(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    if not (await state.get_data()).get("delete_requested"):
        if callback.message is None or not isinstance(callback.message, Message):
            return
        await callback.message.answer(tr("delete_stale"))
        return
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await store.delete_profile(user.id)
    await state.clear()
    await callback.message.answer(
        tr("delete_done"),
        reply_markup=menu(),
    )
