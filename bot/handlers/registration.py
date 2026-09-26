from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.models import Profile, User, utcnow
from bot.i18n import tr
from bot.keyboards.common import genders, inline, location_request, menu
from bot.services.store import Store
from bot.services.telegram import caption
from bot.services.validation import RuleError, age_value, clean_text, normalize_city
from bot.states import Registration

router = Router(name="registration")


async def request_name(message: Message, state: FSMContext) -> None:
    await state.set_state(Registration.name)
    await message.answer(tr("reg_name_prompt"))


async def continue_registration(message: Message, state: FSMContext, user: User) -> None:
    """Resume anketa creation from the username step, preserving recorded consent.

    The one-time 18+/consent screens are skipped for users who already accepted
    them, so the draft must inherit the persisted timestamp. Without this the
    final save would see a photo but no consent and reject a complete anketa.
    """
    if user.consent_at is not None:
        await state.update_data(consent_at=user.consent_at.isoformat())
    if user.username:
        await request_name(message, state)
    else:
        await state.set_state(Registration.username)
        await message.answer(
            tr("username_help"),
            reply_markup=inline(((tr("reg_retry_username"), "reg:username"),)),
        )


@router.callback_query(Registration.adult, F.data == "reg:adult")
async def adult(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    if not isinstance(callback.message, Message):
        return
    # The 18+/consent acceptance is one-time and lives on the user row, so it
    # must be recorded before anything else and survives anketa deletion.
    consent_at = await store.record_consent(user.id)
    await state.update_data(consent_at=consent_at.isoformat())
    await state.set_state(Registration.consent)
    await callback.message.answer(
        tr("consent"),
        reply_markup=inline(
            ((tr("reg_consent_button"), "reg:consent", "success"),),
            ((tr("delete_cancel"), "home:cancel"),),
        ),
    )


@router.callback_query(Registration.consent, F.data == "reg:consent")
async def consent(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    # Redis FSM storage is JSON-backed, so drafts must only contain JSON values.
    await state.update_data(consent_at=utcnow().isoformat())
    await continue_registration(callback.message, state, user)


@router.callback_query(Registration.username, F.data == "reg:username")
async def username(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    if user.username:
        await request_name(callback.message, state)
    else:
        await callback.message.answer(
            tr("username_help"),
            reply_markup=inline(((tr("reg_retry_username"), "reg:username"),)),
        )


@router.message(Registration.name, F.text)
async def name(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    await state.update_data(name=clean_text(message.text, 2, 40))
    await state.set_state(Registration.age)
    await message.answer(tr("reg_age_prompt"))


@router.message(Registration.age, F.text)
async def age(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    await state.update_data(age=age_value(message.text))
    await state.set_state(Registration.gender)
    await message.answer(tr("reg_gender_prompt"), reply_markup=genders("reg:gender"))


@router.callback_query(Registration.gender, F.data.startswith("reg:gender:"))
async def gender(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    value = callback.data.rsplit(":", 1)[-1]
    if value not in {"male", "female"}:
        raise RuleError(tr("err_choose_gender"))
    await state.update_data(gender=value)
    await state.set_state(Registration.seeking)
    await callback.message.answer(
        tr("reg_seeking_prompt"), reply_markup=genders("reg:seeking", True)
    )


@router.callback_query(Registration.seeking, F.data.startswith("reg:seeking:"))
async def seeking(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    value = callback.data.rsplit(":", 1)[-1]
    if value not in {"male", "female", "any"}:
        raise RuleError(tr("err_choose_button"))
    await state.update_data(seeking=value)
    await state.set_state(Registration.location)
    await callback.message.answer(
        tr("reg_location_prompt"),
        reply_markup=location_request(),
    )


@router.message(Registration.location, F.location)
async def location(message: Message, state: FSMContext) -> None:
    if message.location is None:
        return
    city = tr("location_city_default")
    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
        city=city,
        city_normalized=normalize_city(city),
    )
    await state.set_state(Registration.bio)
    await message.answer(
        tr("reg_bio_prompt"),
        reply_markup=inline(((tr("reg_skip_button"), "reg:skip"),)),
    )


async def request_photo(message: Message, state: FSMContext, bio: str) -> None:
    await state.update_data(bio=bio)
    await state.set_state(Registration.photo)
    await message.answer(tr("reg_photo_prompt"))


@router.message(Registration.bio, F.text)
async def bio(message: Message, state: FSMContext) -> None:
    if message.text is None:
        return
    await request_photo(message, state, clean_text(message.text, 0, 300))


@router.callback_query(Registration.bio, F.data == "reg:skip")
async def skip(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await request_photo(callback.message, state, "")


@router.message(Registration.photo, F.photo)
async def photo(message: Message, state: FSMContext) -> None:
    if message.media_group_id or not message.photo:
        raise RuleError(tr("err_album_not_allowed"))
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    draft = await state.get_data()
    await state.set_state(Registration.preview)
    await message.answer_photo(
        draft["photo_file_id"],
        caption=caption(Profile(**draft)),
        reply_markup=inline(
            ((tr("reg_confirm_button"), "reg:save", "success"),),
            ((tr("reg_restart_button"), "reg:restart"),),
        ),
    )


@router.callback_query(Registration.preview, F.data == "reg:save")
async def save(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    draft = await state.get_data()
    # The button is attached to the preview photo, which is authoritative if
    # JSON-backed FSM storage lost or retained a stale draft file_id.
    if isinstance(callback.message, Message) and callback.message.photo:
        draft["photo_file_id"] = callback.message.photo[-1].file_id
    await store.save_profile(user.id, draft)
    await state.clear()
    if not isinstance(callback.message, Message):
        return
    await callback.message.answer(
        tr("reg_done"),
        reply_markup=menu(),
    )


@router.callback_query(Registration.preview, F.data == "reg:restart")
async def restart(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    if not isinstance(callback.message, Message):
        return
    # The user-level consent timestamp outranks any stale draft value; a fresh
    # stamp only covers sessions started before the user-row flag existed.
    consent_at = (await state.get_data()).get("consent_at")
    if user.consent_at is not None:
        consent_at = user.consent_at.isoformat()
    elif consent_at is None:
        consent_at = utcnow().isoformat()
    await state.set_data({"consent_at": consent_at})
    await request_name(callback.message, state)


@router.message(Registration.photo)
async def wrong_photo(message: Message) -> None:
    await message.answer(tr("reg_wrong_photo"))


@router.message(Registration())
async def wrong_input(message: Message) -> None:
    await message.answer(tr("reg_wrong_input"))
