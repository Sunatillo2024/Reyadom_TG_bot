from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import Profile, User, utcnow
from bot.keyboards.common import genders, inline, location_request, menu
from bot.services.store import Store
from bot.services.telegram import caption
from bot.services.validation import RuleError, age_value, clean_text
from bot.states import Registration

router = Router(name="registration")


async def request_name(message: Message, state: FSMContext) -> None:
    await state.set_state(Registration.name)
    await message.answer(
        "<b>Как тебя зовут?</b>\n"
        "Напиши имя для анкеты: от 2 до 40 символов.\n\n"
        "<i>Без контактов и ссылок. /cancel — отмена.</i>"
    )


@router.callback_query(Registration.adult, F.data == "reg:adult")
async def adult(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Registration.consent)
    await callback.message.answer(
        texts.CONSENT,
        reply_markup=inline(
            (("Согласен / согласна", "reg:consent", "success"),),
            (("Отмена", "home:cancel"),),
        ),
    )


@router.callback_query(Registration.consent, F.data == "reg:consent")
async def consent(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    await state.update_data(consent_at=utcnow())
    if user.username:
        await request_name(callback.message, state)
    else:
        await state.set_state(Registration.username)
        await callback.message.answer(
            texts.USERNAME_HELP, reply_markup=inline((("Проверить ещё раз", "reg:username"),))
        )


@router.callback_query(Registration.username, F.data == "reg:username")
async def username(callback: CallbackQuery, state: FSMContext, user: User) -> None:
    if user.username:
        await request_name(callback.message, state)
    else:
        await callback.message.answer(
            texts.USERNAME_HELP, reply_markup=inline((("Проверить ещё раз", "reg:username"),))
        )


@router.message(Registration.name, F.text)
async def name(message: Message, state: FSMContext) -> None:
    await state.update_data(name=clean_text(message.text, 2, 40))
    await state.set_state(Registration.age)
    await message.answer("<b>Сколько тебе лет?</b>\nОтправь возраст целым числом от 18 до 99.")


@router.message(Registration.age, F.text)
async def age(message: Message, state: FSMContext) -> None:
    await state.update_data(age=age_value(message.text))
    await state.set_state(Registration.gender)
    await message.answer("<b>Укажи свой пол</b>", reply_markup=genders("reg:gender"))


@router.callback_query(Registration.gender, F.data.startswith("reg:gender:"))
async def gender(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    if value not in {"male", "female"}:
        raise RuleError("Выбери пол с помощью кнопки.")
    await state.update_data(gender=value)
    await state.set_state(Registration.seeking)
    await callback.message.answer(
        "<b>Кого ты ищешь?</b>", reply_markup=genders("reg:seeking", True)
    )


@router.callback_query(Registration.seeking, F.data.startswith("reg:seeking:"))
async def seeking(callback: CallbackQuery, state: FSMContext) -> None:
    value = callback.data.rsplit(":", 1)[-1]
    if value not in {"male", "female", "any"}:
        raise RuleError("Нажми одну из кнопок.")
    await state.update_data(seeking=value)
    await state.set_state(Registration.location)
    await callback.message.answer(
        "<b>Где ты находишься? 📍</b>\n"
        "Отправь геолокацию кнопкой ниже. Сначала покажем людей ближе к тебе, "
        "затем — тех, кто дальше.\n\n"
        "<i>Точные координаты другим пользователям не показываются.</i>",
        reply_markup=location_request(),
    )


@router.message(Registration.location, F.location)
async def location(message: Message, state: FSMContext) -> None:
    await state.update_data(
        latitude=message.location.latitude,
        longitude=message.location.longitude,
        city="Геолокация",
        city_normalized="геолокация",
    )
    await state.set_state(Registration.bio)
    await message.answer(
        "<b>Расскажи о себе</b>\n"
        "Напиши до 300 символов или пропусти этот шаг.\n\n"
        "<i>Не указывай @username и ссылки.</i>",
        reply_markup=inline((("Пропустить", "reg:skip"),)),
    )


async def request_photo(message: Message, state: FSMContext, bio: str) -> None:
    await state.update_data(bio=bio)
    await state.set_state(Registration.photo)
    await message.answer(
        "<b>Добавь фотографию</b>\n"
        "Отправь одно своё фото как фотографию в Telegram.\n\n"
        "<i>Файл или видео не подойдут.</i>"
    )


@router.message(Registration.bio, F.text)
async def bio(message: Message, state: FSMContext) -> None:
    await request_photo(message, state, clean_text(message.text, 0, 300))


@router.callback_query(Registration.bio, F.data == "reg:skip")
async def skip(callback: CallbackQuery, state: FSMContext) -> None:
    await request_photo(callback.message, state, "")


@router.message(Registration.photo, F.photo)
async def photo(message: Message, state: FSMContext) -> None:
    if message.media_group_id:
        raise RuleError("Отправь только одно фото, без альбома.")
    await state.update_data(photo_file_id=message.photo[-1].file_id)
    draft = await state.get_data()
    await state.set_state(Registration.preview)
    await message.answer_photo(
        draft["photo_file_id"],
        caption=caption(Profile(**draft)),
        reply_markup=inline(
            (("Подтвердить", "reg:save", "success"),),
            (("Заполнить заново", "reg:restart"),),
        ),
    )


@router.callback_query(Registration.preview, F.data == "reg:save")
async def save(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    await store.save_profile(user.id, await state.get_data())
    await state.clear()
    await callback.message.answer(
        "<b>Готово! Анкета создана 💜</b>\n"
        "Поиск настроен на возраст 18–99 лет. Анкеты будут показаны от ближайших "
        "к более дальним. Геолокацию можно изменить в настройках.",
        reply_markup=menu(),
    )


@router.callback_query(Registration.preview, F.data == "reg:restart")
async def restart(callback: CallbackQuery, state: FSMContext) -> None:
    consent_at = (await state.get_data())["consent_at"]
    await state.set_data({"consent_at": consent_at})
    await request_name(callback.message, state)


@router.message(Registration.photo)
async def wrong_photo(message: Message) -> None:
    await message.answer(
        "Отправь одну фотографию как фото. Видео, файл и текст не подойдут.\n\n"
        "<i>/cancel — отмена.</i>"
    )


@router.message(Registration())
async def wrong_input(message: Message) -> None:
    await message.answer(
        "Ответь на текущий вопрос или нажми подходящую кнопку. "
        "/cancel — отмена, /start — начать заново."
    )
