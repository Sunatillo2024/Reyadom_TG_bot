from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot.db.models import User
from bot.i18n import localized_labels, tr
from bot.keyboards.common import inline, menu
from bot.services.payments import PaymentService
from bot.services.premium import PREMIUM_PLANS, plan_label, premium_status
from bot.services.store import Store
from bot.services.validation import RuleError

router = Router(name="premium")


def premium_keyboard(is_premium: bool = False) -> InlineKeyboardMarkup:
    """Build Premium menu keyboard with plan buttons."""
    rows = []
    for plan_code, plan_info in PREMIUM_PLANS.items():
        if plan_code == "premium_3d":
            label = f"{tr('premium_try')}: {tr('plan_3d')} · {plan_info['price_stars']} ⭐️"
        elif plan_code == "premium_3m":
            label = f"🔥 {tr('plan_3m')} · {plan_info['price_stars']} ⭐️"
        else:
            label = f"{tr('plan_1m')} · {plan_info['price_stars']} ⭐️"
        rows.append(((label, f"premium:plan:{plan_code}"),))

    if is_premium:
        rows.append(((tr("premium_settings"), "premium:settings"),))

    rows.append(((tr("premium_home"), "home"),))
    return inline(*rows)


@router.message(F.text.in_(localized_labels("menu_premium")))
@router.callback_query(F.data == "premium")
async def premium_menu(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()

    status = premium_status(user)

    if status.is_premium and status.until:
        key = "premium_paid_active" if status.kind == "paid" else "premium_trial_active"
        text = tr(key, until=status.until.strftime("%d.%m.%Y %H:%M UTC"))
    else:
        text = tr("premium_intro")

    message = event.message if isinstance(event, CallbackQuery) else event
    if not isinstance(message, Message):
        return

    await message.answer(text, reply_markup=premium_keyboard(status.is_premium))


@router.callback_query(F.data.startswith("premium:plan:"))
async def premium_plan(callback: CallbackQuery, store: Store, user: User) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return

    plan_code = callback.data.split(":", 2)[2]
    if plan_code not in PREMIUM_PLANS:
        raise RuleError(tr("err_invalid_tariff"))

    order = await PaymentService(store).create_or_reuse_order(
        user.id, callback.from_user.id, plan_code
    )
    await callback.message.answer(
        tr(
            "premium_plan_details",
            plan=plan_label(plan_code),
            price=order.price_stars,
        ),
        reply_markup=inline(
            ((tr("premium_accept"), f"pay:confirm:{order.id}", "success"),),
            ((tr("premium_terms"), "pay:terms"),),
            ((tr("premium_other"), "premium"), (tr("premium_home"), "home")),
        ),
    )


@router.callback_query(F.data == "premium:settings")
async def premium_settings(callback: CallbackQuery, store: Store, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    status = premium_status(user)
    if not status.is_premium:
        raise RuleError(tr("err_premium_only"))

    badge_key = "premium_badge_shown" if user.show_premium_badge else "premium_badge_hidden"

    await callback.message.answer(
        tr("premium_settings_text", badge=tr(badge_key)),
        reply_markup=inline(
            (
                (
                    tr(
                        "premium_badge_hide_button"
                        if user.show_premium_badge
                        else "premium_badge_show_button"
                    ),
                    "premium:badge:toggle",
                ),
            ),
            ((tr("menu_premium"), "premium"), (tr("premium_home"), "home")),
        ),
    )


@router.callback_query(F.data == "premium:badge:toggle")
async def toggle_badge(callback: CallbackQuery, store: Store, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    status = premium_status(user)
    if not status.is_premium:
        raise RuleError(tr("err_premium_only"))

    new_status = await store.toggle_premium_badge(user.id)
    badge_key = "premium_badge_shown" if new_status else "premium_badge_hidden"
    await callback.message.answer(
        tr("premium_badge_done", badge=tr(badge_key)),
        reply_markup=menu(),
    )
