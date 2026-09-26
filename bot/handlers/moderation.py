from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from bot.db.models import User
from bot.i18n import tr
from bot.keyboards.common import home, inline
from bot.services.store import Store
from bot.services.telegram import safe_call, target_id
from bot.services.validation import RuleError
from bot.states import Complaint

router = Router(name="moderation")
# Lexicon keys of the report reasons; the label is resolved in the user's language.
REASONS = {
    "spam": "reason_spam",
    "fake": "reason_fake",
    "content": "reason_content",
    "other": "reason_other",
}


def get_callback_message(callback: CallbackQuery) -> Message:
    message = callback.message
    if not isinstance(message, Message):
        raise RuleError(tr("err_message_unavailable"))
    return message


def get_callback_data(callback: CallbackQuery) -> str:
    data = callback.data
    if data is None:
        raise RuleError(tr("err_invalid_command"))
    return data


@router.callback_query(F.data.startswith("block:"))
async def block(callback: CallbackQuery, store: Store, user: User) -> None:
    message = get_callback_message(callback)
    target = target_id(get_callback_data(callback).split(":", 1)[1])
    await store.block(user.id, target)
    await safe_call(store, user.telegram_id, lambda: message.edit_reply_markup(reply_markup=None))
    await message.answer(
        tr("blocked_notice"),
        reply_markup=home(),
    )


@router.callback_query(F.data.startswith("report:"))
async def report_begin(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    message = get_callback_message(callback)
    target = target_id(get_callback_data(callback).split(":", 1)[1])
    await store.validate_target(user.id, target)
    await state.clear()
    await state.set_state(Complaint.reason)
    await state.update_data(target=target)
    await message.answer(
        tr("report_reason_prompt"),
        reply_markup=inline(
            *[((tr(label_key), f"reason:{key}"),) for key, label_key in REASONS.items()]
        ),
    )


async def confirm_prompt(message: Message, state: FSMContext, reason: str) -> None:
    await state.update_data(reason=reason)
    await state.set_state(Complaint.confirm)
    await message.answer(
        tr("report_confirm_prompt"),
        reply_markup=inline(
            ((tr("report_send"), "reportconfirm", "danger"),),
            ((tr("delete_cancel"), "home:cancel"),),
        ),
    )


@router.callback_query(Complaint.reason, F.data.startswith("reason:"))
async def reason(callback: CallbackQuery, state: FSMContext) -> None:
    message = get_callback_message(callback)
    key = get_callback_data(callback).split(":", 1)[1]
    if key not in REASONS:
        raise RuleError(tr("err_choose_reason"))
    if key == "other":
        await state.set_state(Complaint.comment)
        await message.answer(tr("report_comment_prompt"))
    else:
        await confirm_prompt(message, state, tr(REASONS[key]))


@router.message(Complaint.comment)
async def comment(message: Message, state: FSMContext) -> None:
    value = (message.text or "").strip()
    if not 1 <= len(value) <= 300:
        raise RuleError(tr("err_comment_length"))
    await confirm_prompt(message, state, tr("reason_other_value", value=value))


@router.callback_query(Complaint.confirm, F.data == "reportconfirm")
async def report_confirm(
    callback: CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    message = get_callback_message(callback)
    draft = await state.get_data()
    await store.report(user.id, draft["target"], draft["reason"])
    await state.clear()
    await safe_call(store, user.telegram_id, lambda: message.edit_reply_markup(reply_markup=None))
    await message.answer(tr("report_saved"), reply_markup=home())
