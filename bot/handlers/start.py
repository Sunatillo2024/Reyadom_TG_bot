from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import inline, menu
from bot.services.store import Store
from bot.services.telegram import navigate
from bot.states import Registration

router = Router(name="start")


async def show_home(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()
    if user.is_banned:
        await navigate(
            event,
            "<b>Доступ ограничен</b>\nТы можешь использовать /help, /privacy, /id и /delete.",
            menu(),
        )
        return
    profile = await store.profile(user.id)
    if profile:
        # Keeping the home screen as a media message lets Telegram replace both
        # its photo and caption while the user navigates to other profiles.
        await navigate(event, texts.HOME, menu(), photo=profile.photo_file_id)
    else:
        await state.set_state(Registration.adult)
        await navigate(
            event,
            texts.INTRO,
            inline(
                (("Мне уже есть 18 лет", "reg:adult", "primary"),),
                (("Отмена", "home:cancel"),),
            ),
        )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await show_home(message, state, store, user)


@router.callback_query(F.data == "home")
async def home(callback: CallbackQuery, state: FSMContext, store: Store, user: User) -> None:
    await show_home(callback, state, store, user)


@router.message(Command("cancel"))
@router.callback_query(F.data == "home:cancel")
async def cancel(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await navigate(event, "Действие отменено. Сохранённая анкета не изменилась.", menu())


@router.message(Command("help"))
@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[5]))
@router.callback_query(F.data == "help")
async def help_message(event: Message | CallbackQuery) -> None:
    await navigate(event, texts.HELP, inline((("🏠 В меню", "home"),)))


@router.message(Command("privacy"))
async def privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY)


@router.message(Command("id"))
async def own_id(message: Message) -> None:
    await message.answer(f"Твой Telegram ID: <code>{message.from_user.id}</code>")


@router.message(Command("delete"))
@router.callback_query(F.data == "delete")
async def delete_prompt(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(delete_requested=True)
    await navigate(
        event,
        texts.DELETE_NOTICE,
        inline(
            (("Да, удалить", "delete:yes", "danger"),), (("Отмена", "home:cancel"),)
        ),
    )


@router.callback_query(F.data == "delete:yes")
async def delete_confirm(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    if not (await state.get_data()).get("delete_requested"):
        await navigate(
            callback,
            "Подтверждение устарело. Начни заново с /delete.",
            inline((("🏠 В меню", "home"),)),
        )
        return
    await store.delete_profile(user.id)
    await state.clear()
    await navigate(
        callback,
        "<b>Анкета удалена</b>\n"
        "Связанные реакции и взаимные симпатии удалены. Записи модерации сохранены.",
        menu(),
    )
