from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import genders, inline, location_request, menu, profile_menu
from bot.services.store import Store
from bot.services.telegram import caption, navigate
from bot.services.validation import RuleError, age_range
from bot.states import Edit, Search

router = Router(name="profile")


async def show_saved(
    event: Message | CallbackQuery, store: Store, user: User
) -> None:
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError("Анкета не найдена.")
    await navigate(event, texts.PROFILE_SAVED, menu(), photo=profile.photo_file_id)


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[1]))
@router.callback_query(F.data == "profile")
async def my_profile(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError("Анкета не найдена. Создай её с помощью /start.")
    text = caption(profile) + "\n\n<b>Статус анкеты:</b> " + (
        "активна" if profile.is_active else "скрыта"
    )
    await navigate(
        event, text, profile_menu(profile.is_active), photo=profile.photo_file_id
    )


@router.callback_query(F.data.startswith("edit:"))
async def edit_begin(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
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
    keyboard = inline((("Отмена", "home:cancel"),))
    if field in {"gender", "seeking"}:
        keyboard = genders("editvalue", field == "seeking")
    if field == "location":
        keyboard = location_request()
    if field == "bio":
        keyboard = inline(
            (("Очистить описание", "editvalue:empty"),),
            (("Отмена", "home:cancel"),),
        )
    prompt = prompts[field] + "\n\n<i>/cancel — отменить без сохранения.</i>"
    if field == "location":
        # Reply keyboards cannot be installed with editMessageReplyMarkup.
        await callback.message.answer(prompt, reply_markup=keyboard)
    else:
        await navigate(callback, prompt, keyboard)


@router.message(Edit.value)
async def edit_value(message: Message, state: FSMContext, store: Store, user: User) -> None:
    field = (await state.get_data())["field"]
    if field == "location":
        if not message.location:
            raise RuleError("Отправь геолокацию с помощью кнопки ниже.")
        await store.edit_location(user.id, message.location.latitude, message.location.longitude)
        await state.clear()
        await show_saved(message, store, user)
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
    await show_saved(message, store, user)


@router.callback_query(Edit.value, F.data.startswith("editvalue:"))
async def edit_choice(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    field = (await state.get_data())["field"]
    value = callback.data.split(":", 1)[1]
    if field not in {"gender", "seeking", "bio"} or (field == "bio" and value != "empty"):
        raise RuleError("Эта кнопка сейчас недоступна.")
    await store.edit_profile(user.id, field, "" if value == "empty" else value)
    await state.clear()
    await show_saved(callback, store, user)


@router.callback_query(F.data.in_({"active:0", "active:1"}))
async def active(callback: CallbackQuery, store: Store, user: User) -> None:
    enabled = callback.data == "active:1"
    await store.set_active(user.id, enabled)
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError("Анкета не найдена.")
    status = (
        "<b>Анкета снова видна 💜</b>\nТеперь её могут увидеть другие пользователи."
        if enabled
        else "<b>Анкета скрыта</b>\nНовые пользователи не увидят её в поиске."
    )
    await navigate(
        callback,
        caption(profile) + "\n\n" + status,
        profile_menu(enabled),
        photo=profile.photo_file_id,
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
    location_status = "указана" if profile.latitude is not None else "не указана"
    await navigate(
        event,
        f"<b>⚙️ Настройки поиска</b>\n"
        f"Возраст: {profile.min_age}–{profile.max_age}\n"
        f"Геолокация: {location_status}",
        inline(
            (("Возраст для поиска", "settings:age"),),
            (("📍 Изменить геолокацию", "edit:location"),),
            (("Кого я ищу", "edit:seeking"), ("🏠 В меню", "home")),
        ),
    )


@router.callback_query(F.data == "settings:age")
async def age_begin(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(Search.age)
    await navigate(
        callback,
        "<b>Возраст для поиска</b>\n"
        "Отправь минимальный и максимальный возраст через пробел, например: 20 35.\n\n"
        "<i>18 ≤ минимум ≤ максимум ≤ 99. /cancel — отмена.</i>",
        inline((("Отмена", "home:cancel"),)),
    )


@router.message(Search.age)
async def age_save(message: Message, state: FSMContext, store: Store, user: User) -> None:
    parts = (message.text or "").split()
    if len(parts) != 2:
        raise RuleError("Отправь два целых числа, например: 20 35.")
    low, high = age_range(*parts)
    profile = await store.profile(user.id)
    if not profile:
        raise RuleError("Анкета не найдена.")
    await store.settings(user.id, low, high, profile.own_city_only)
    await state.clear()
    await navigate(
        message,
        "<b>Готово!</b> Настройки поиска сохранены 💜",
        menu(),
        photo=profile.photo_file_id,
    )
