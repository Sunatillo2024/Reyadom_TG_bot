from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.i18n import localized_labels, tr
from bot.keyboards.common import genders, inline, location_request, menu, profile_menu
from bot.services.store import Store
from bot.services.telegram import caption
from bot.services.validation import RuleError, age_range
from bot.states import Edit, Search

router = Router(name="profile")


@router.message(F.text.in_(localized_labels("menu_profile")))
async def my_profile(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    profile = await store.profile(user.id)
    if not profile:
        await message.answer(tr("profile_missing"))
        return
    try:
        await message.answer_photo(
            profile.photo_file_id,
            caption=caption(profile),
            reply_markup=profile_menu(profile.is_active),
        )
    except TelegramBadRequest:
        await message.answer(
            caption(profile) + "\n\n<i>" + tr("profile_photo_error") + "</i>",
            reply_markup=profile_menu(profile.is_active),
        )
    await message.answer(
        tr("profile_status_active" if profile.is_active else "profile_status_hidden")
    )


@router.callback_query(F.data.startswith("edit:"))
async def edit_begin(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    field = callback.data.split(":", 1)[1]
    prompts = {
        "name": tr("edit_name"),
        "age": tr("edit_age"),
        "city": tr("edit_city"),
        "bio": tr("edit_bio"),
        "gender": tr("edit_gender"),
        "seeking": tr("edit_seeking"),
        "location": tr("edit_location"),
        "photo_file_id": tr("edit_photo"),
    }
    if field not in prompts or not await store.profile(user.id):
        raise RuleError(tr("err_profile_field_missing"))
    await state.clear()
    await state.set_state(Edit.value)
    await state.update_data(field=field)
    keyboard = None
    if field in {"gender", "seeking"}:
        keyboard = genders("editvalue", field == "seeking")
    if field == "location":
        keyboard = location_request()
    if field == "bio":
        keyboard = inline(((tr("edit_clear_bio"), "editvalue:empty"),))
    await callback.message.answer(
        prompts[field] + tr("edit_cancel_hint"), reply_markup=keyboard
    )


@router.message(Edit.value)
async def edit_value(message: Message, state: FSMContext, store: Store, user: User) -> None:
    field = (await state.get_data())["field"]
    if field == "location":
        if not message.location:
            raise RuleError(tr("err_location_button"))
        await store.edit_location(user.id, message.location.latitude, message.location.longitude)
        await state.clear()
        await message.answer(tr("profile_saved"), reply_markup=menu())
        return
    if field == "photo_file_id":
        if not message.photo or message.media_group_id:
            raise RuleError(tr("err_one_photo_photo"))
        value = message.photo[-1].file_id
    elif field in {"gender", "seeking"}:
        raise RuleError(tr("err_use_buttons_above"))
    elif message.text:
        value = message.text
    else:
        raise RuleError(tr("err_send_text_or_cancel"))
    await store.edit_profile(user.id, field, value)
    await state.clear()
    await message.answer(tr("profile_saved"), reply_markup=menu())


@router.callback_query(Edit.value, F.data.startswith("editvalue:"))
async def edit_choice(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    field = (await state.get_data())["field"]
    value = callback.data.split(":", 1)[1]
    if field not in {"gender", "seeking", "bio"} or (field == "bio" and value != "empty"):
        raise RuleError(tr("err_button_unavailable"))
    await store.edit_profile(user.id, field, "" if value == "empty" else value)
    await state.clear()
    await callback.message.answer(tr("profile_saved"), reply_markup=menu())


@router.callback_query(F.data.in_({"active:0", "active:1"}))
async def active(callback: CallbackQuery, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    enabled = callback.data == "active:1"
    await store.set_active(user.id, enabled)
    await callback.message.answer(
        tr("profile_visible" if enabled else "profile_hidden"),
        reply_markup=profile_menu(enabled),
    )


@router.message(F.text.in_(localized_labels("menu_settings")))
@router.callback_query(F.data == "settings")
async def settings(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError(tr("err_create_profile"))
    if isinstance(event, CallbackQuery):
        if not isinstance(event.message, Message):
            return
        message = event.message
    else:
        message = event
    location_status = tr("location_set" if profile.latitude is not None else "location_unset")
    await message.answer(
        tr(
            "search_settings",
            min_age=profile.min_age,
            max_age=profile.max_age,
            location=location_status,
        ),
        reply_markup=inline(
            ((tr("age_search"), "settings:age"),),
            ((tr("change_location"), "edit:location"),),
            ((tr("seeking_label"), "edit:seeking"), (tr("back_menu"), "home")),
            ((tr("change_language"), "settings:language"),),
        ),
    )


@router.callback_query(F.data == "settings:age")
async def age_begin(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await state.clear()
    await state.set_state(Search.age)
    await callback.message.answer(tr("age_search_prompt"))


@router.message(Search.age)
async def age_save(message: Message, state: FSMContext, store: Store, user: User) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2:
        raise RuleError(tr("err_two_ints"))
    try:
        low, high = int(parts[0]), int(parts[1])
    except ValueError:
        raise RuleError(tr("err_ints_expected")) from None
    low, high = age_range(low, high)
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError(tr("err_profile_not_found"))
    await store.settings(user.id, low, high, profile.own_city_only)
    await state.clear()
    await message.answer(tr("search_saved"), reply_markup=menu())
