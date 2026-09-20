from aiogram import F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import genders, inline, location_request, menu, profile_menu
from bot.services.store import Store
from bot.services.telegram import caption
from bot.services.validation import RuleError, age_range
from bot.states import Edit, Search

router = Router(name="profile")


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[1]))
async def my_profile(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    profile = await store.profile(user.id)
    if not profile:
        await message.answer("Анкета не найдена. Создай её с помощью /start.")
        return
    try:
        await message.answer_photo(
            profile.photo_file_id,
            caption=caption(profile),
            reply_markup=profile_menu(profile.is_active),
        )
    except TelegramBadRequest:
        await message.answer(
            caption(profile)
            + "\n\n<i>Не удалось открыть прежнюю фотографию. Нажми «Фото» и загрузи новую.</i>",
            reply_markup=profile_menu(profile.is_active),
        )
    await message.answer("<b>Статус анкеты:</b> " + ("активна" if profile.is_active else "скрыта"))


@router.callback_query(F.data.startswith("edit:"))
async def edit_begin(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    field = callback.data.split(":", 1)[1]
    prompts = {
        "name": "<b>Новое имя</b>\nОтправь от 2 до 40 символов.",
        "age": "<b>Новый возраст</b>\nОтправь целое число от 18 до 99.",
        "city": "<b>Новый город</b>\nОтправь от 2 до 60 символов.",
        "bio": "<b>Новое описание</b>\nОтправь до 300 символов.",
        "gender": "<b>Выбери пол</b>",
        "seeking": "<b>Кого ты ищешь?</b>",
        "location": "<b>Новое местоположение 📍</b>\nОтправь геолокацию кнопкой ниже.",
        "photo_file_id": "<b>Новое фото</b>\nОтправь одну фотографию как фото.",
    }
    if field not in prompts or not await store.profile(user.id):
        raise RuleError("Анкета или поле не найдены.")
    await state.clear()
    await state.set_state(Edit.value)
    await state.update_data(field=field)
    keyboard = None
    if field in {"gender", "seeking"}:
        keyboard = genders("editvalue", field == "seeking")
    if field == "location":
        keyboard = location_request()
    if field == "bio":
        keyboard = inline((("Очистить описание", "editvalue:empty"),))
    await callback.message.answer(
        prompts[field] + "\n\n<i>/cancel — отменить без сохранения.</i>", reply_markup=keyboard
    )


@router.message(Edit.value)
async def edit_value(message: Message, state: FSMContext, store: Store, user: User) -> None:
    field = (await state.get_data())["field"]
    if field == "location":
        if not message.location:
            raise RuleError("Отправь геолокацию с помощью кнопки ниже.")
        await store.edit_location(user.id, message.location.latitude, message.location.longitude)
        await state.clear()
        await message.answer(texts.PROFILE_SAVED, reply_markup=menu())
        return
    if field == "photo_file_id":
        if not message.photo or message.media_group_id:
            raise RuleError("Отправь одну фотографию как фото, а не файл или видео.")
        value = message.photo[-1].file_id
    elif field in {"gender", "seeking"}:
        raise RuleError("Выбери вариант с помощью кнопок выше.")
    elif message.text:
        value = message.text
    else:
        raise RuleError("Отправь текст или используй /cancel.")
    await store.edit_profile(user.id, field, value)
    await state.clear()
    await message.answer(texts.PROFILE_SAVED, reply_markup=menu())


@router.callback_query(Edit.value, F.data.startswith("editvalue:"))
async def edit_choice(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    field = (await state.get_data())["field"]
    value = callback.data.split(":", 1)[1]
    if field not in {"gender", "seeking", "bio"} or (field == "bio" and value != "empty"):
        raise RuleError("Эта кнопка сейчас недоступна.")
    await store.edit_profile(user.id, field, "" if value == "empty" else value)
    await state.clear()
    await callback.message.answer(texts.PROFILE_SAVED, reply_markup=menu())


@router.callback_query(F.data.in_({"active:0", "active:1"}))
async def active(callback: CallbackQuery, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    enabled = callback.data == "active:1"
    await store.set_active(user.id, enabled)
    await callback.message.answer(
        (
            "<b>Анкета снова видна 💜</b>\nТеперь её могут увидеть другие пользователи."
            if enabled
            else "<b>Анкета скрыта</b>\nНовые пользователи не увидят её в поиске."
        ),
        reply_markup=profile_menu(enabled),
    )


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[4]))
@router.callback_query(F.data == "settings")
async def settings(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError("Сначала создай анкету с помощью /start.")
    if isinstance(event, CallbackQuery):
        if not isinstance(event.message, Message):
            return
        message = event.message
    else:
        message = event
    location_status = "указана" if profile.latitude is not None else "не указана"
    await message.answer(
        f"<b>⚙️ Настройки поиска</b>\n"
        f"Возраст: {profile.min_age}–{profile.max_age}\n"
        f"Геолокация: {location_status}",
        reply_markup=inline(
            (("Возраст для поиска", "settings:age"),),
            (("📍 Изменить геолокацию", "edit:location"),),
            (("Кого я ищу", "edit:seeking"), ("🏠 В меню", "home")),
        ),
    )


@router.callback_query(F.data == "settings:age")
async def age_begin(callback: CallbackQuery, state: FSMContext) -> None:
    if not isinstance(callback.message, Message):
        return
    await state.clear()
    await state.set_state(Search.age)
    await callback.message.answer(
        "<b>Возраст для поиска</b>\n"
        "Отправь минимальный и максимальный возраст через пробел, например: 20 35.\n\n"
        "<i>18 ≤ минимум ≤ максимум ≤ 99. /cancel — отмена.</i>"
    )


@router.message(Search.age)
async def age_save(message: Message, state: FSMContext, store: Store, user: User) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2:
        raise RuleError("Отправь два целых числа, например: 20 35.")
    try:
        low, high = age_range(int(parts[0]), int(parts[1]))
    except ValueError:
        raise RuleError("Возраст должен быть указан двумя целыми числами, например: 20 35.")
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError("Анкета не найдена.")
    await store.settings(user.id, low, high, profile.own_city_only)
    await state.clear()
    await message.answer("<b>Готово!</b> Настройки поиска сохранены 💜", reply_markup=menu())
