from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import inline, menu
from bot.services.store import Store
from bot.states import Registration

router = Router(name="start")


async def show_home(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await state.clear()
    if user.is_banned:
        await message.answer(
            "<b>Доступ ограничен</b>\nТы можешь использовать /help, /privacy, /id и /delete.",
            reply_markup=menu(),
        )
    elif await store.profile(user.id):
        await message.answer(texts.HOME, reply_markup=menu())
    else:
        await state.set_state(Registration.adult)
        await message.answer(
            texts.INTRO,
            reply_markup=inline(
                (("Мне уже есть 18 лет", "reg:adult", "primary"),),
                (("Отмена", "home:cancel"),),
            ),
        )


@router.message(CommandStart())
async def start(message: Message, state: FSMContext, store: Store, user: User) -> None:
    await show_home(message, state, store, user)


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
        "Действие отменено. Сохранённая анкета не изменилась.", reply_markup=menu()
    )


@router.message(Command("help"))
@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[5]))
async def help_message(message: Message) -> None:
    await message.answer(texts.HELP)


@router.message(Command("privacy"))
async def privacy(message: Message) -> None:
    await message.answer(texts.PRIVACY)


@router.message(Command("id"))
async def own_id(message: Message) -> None:
    if message.from_user is None:
        return
    await message.answer(f"Твой Telegram ID: <code>{message.from_user.id}</code>")


@router.message(Command("delete"))
@router.callback_query(F.data == "delete")
async def delete_prompt(event: Message | CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await state.update_data(delete_requested=True)
    message = event.message if isinstance(event, CallbackQuery) else event
    if message is None or not isinstance(message, Message):
        return
    await message.answer(
        texts.DELETE_NOTICE,
        reply_markup=inline(
            (("Да, удалить", "delete:yes", "danger"),), (("Отмена", "home:cancel"),)
        ),
    )


@router.callback_query(F.data == "delete:yes")
async def delete_confirm(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    if not (await state.get_data()).get("delete_requested"):
        if callback.message is None or not isinstance(callback.message, Message):
            return
        await callback.message.answer("Подтверждение устарело. Начни заново с /delete.")
        return
    if callback.message is None or not isinstance(callback.message, Message):
        return
    await store.delete_profile(user.id)
    await state.clear()
    await callback.message.answer(
        "<b>Анкета удалена</b>\n"
        "Связанные реакции и взаимные симпатии удалены. Записи модерации сохранены.",
        reply_markup=menu(),
    )
