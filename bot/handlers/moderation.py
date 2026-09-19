from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.keyboards.common import home, inline
from bot.services.store import Store
from bot.services.telegram import navigate, target_id
from bot.services.validation import RuleError
from bot.states import Complaint

router = Router(name="moderation")
REASONS = {
    "spam": "Спам",
    "fake": "Фальшивая анкета",
    "content": "Недопустимый контент",
    "other": "Другое",
}


@router.callback_query(F.data.startswith("block:"))
async def block(callback: CallbackQuery, store: Store, user: User) -> None:
    target = target_id(callback.data.split(":", 1)[1])
    await store.block(user.id, target)
    await navigate(
        callback,
        "<b>Пользователь заблокирован</b>\n"
        "Анкеты больше не будут видны друг другу в боте, а контакт станет недоступен.\n\n"
        "<i>В личном чате Telegram пользователя можно заблокировать отдельно.</i>",
        home(),
    )


@router.callback_query(F.data.startswith("report:"))
async def report_begin(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    target = target_id(callback.data.split(":", 1)[1])
    await store.validate_target(user.id, target)
    await state.clear()
    await state.set_state(Complaint.reason)
    await state.update_data(target=target)
    reason_rows = [((label, f"reason:{key}"),) for key, label in REASONS.items()]
    await navigate(
        callback,
        "<b>Почему ты хочешь пожаловаться?</b>\nВыбери причину ниже.\n\n<i>/cancel — отмена.</i>",
        inline(*reason_rows, (("Отмена", "home:cancel"),)),
    )


async def confirm_prompt(
    event: Message | CallbackQuery, state: FSMContext, reason: str
) -> None:
    await state.update_data(reason=reason)
    await state.set_state(Complaint.confirm)
    await navigate(
        event,
        "<b>Отправить жалобу?</b>\n"
        "Её увидят администраторы, а анкета будет заблокирована для тебя. "
        "Пользователь не узнает, кто отправил жалобу.",
        inline(
            (("Отправить жалобу", "reportconfirm", "danger"),),
            (("Отмена", "home:cancel"),),
        ),
    )


@router.callback_query(Complaint.reason, F.data.startswith("reason:"))
async def reason(callback: CallbackQuery, state: FSMContext) -> None:
    key = callback.data.split(":", 1)[1]
    if key not in REASONS:
        raise RuleError("Выбери причину с помощью кнопки.")
    if key == "other":
        await state.set_state(Complaint.comment)
        await navigate(
            callback,
            "<b>Опиши причину</b>\n"
            "Напиши комментарий длиной от 1 до 300 символов.\n\n"
            "<i>/cancel — отмена.</i>",
            inline((("Отмена", "home:cancel"),)),
        )
    else:
        await confirm_prompt(callback, state, REASONS[key])


@router.message(Complaint.comment)
async def comment(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not 1 <= len(value) <= 300:
        raise RuleError("Комментарий должен содержать 1–300 символов.")
    await confirm_prompt(message, state, "Другое: " + value)


@router.callback_query(Complaint.confirm, F.data == "reportconfirm")
async def report_confirm(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    draft = await state.get_data()
    await store.report(user.id, draft["target"], draft["reason"])
    await state.clear()
    await navigate(
        callback,
        "<b>Жалоба сохранена</b>\nАнкета заблокирована для тебя.",
        home(),
    )
