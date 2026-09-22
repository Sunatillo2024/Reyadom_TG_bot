from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from bot import texts
from bot.db.models import User
from bot.keyboards.common import inline, menu
from bot.services.payments import PaymentService
from bot.services.premium import PREMIUM_PLANS, premium_status
from bot.services.store import Store
from bot.services.validation import RuleError

router = Router(name="premium")


def premium_keyboard(is_premium: bool = False) -> InlineKeyboardMarkup:
    """Build Premium menu keyboard with plan buttons."""
    rows = []
    for plan_code, plan_info in PREMIUM_PLANS.items():
        if plan_code == "premium_3d":
            label = f"Попробовать на {plan_info['label']} · {plan_info['price_stars']} ⭐️"
        elif plan_code == "premium_3m":
            label = f"🔥 {plan_info['label']} · {plan_info['price_stars']} ⭐️"
        else:
            label = f"{plan_info['label']} · {plan_info['price_stars']} ⭐️"
        rows.append(((label, f"premium:plan:{plan_code}"),))

    if is_premium:
        rows.append((("⚙️ Настройки Premium", "premium:settings"),))

    rows.append((("🏠 В меню", "home"),))
    return inline(*rows)


@router.message(F.text.in_(texts.MENU_LABEL_ALIASES[5]))
@router.callback_query(F.data == "premium")
async def premium_menu(
    event: Message | CallbackQuery, state: FSMContext, store: Store, user: User
) -> None:
    await state.clear()

    status = premium_status(user)

    if status.is_premium and status.until:
        template = (
            texts.PREMIUM_PAID_ACTIVE
            if status.kind == "paid"
            else texts.PREMIUM_TRIAL_ACTIVE
        )
        text = template.format(until=status.until.strftime("%d.%m.%Y %H:%M UTC"))
    else:
        text = texts.PREMIUM_INTRO

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
        raise RuleError("Недействительный тариф.")

    order = await PaymentService(store).create_or_reuse_order(
        user.id, callback.from_user.id, plan_code
    )
    plan = PREMIUM_PLANS[plan_code]
    await callback.message.answer(
        f"<b>💎 Premium на {plan['label']}</b>\n\n"
        f"Стоимость: <b>{order.price_stars} ⭐️</b>\n"
        f"Срок: <b>{plan['label']}</b>\n"
        "Тип покупки: <b>разовая, без автосписания</b>\n\n"
        "Новый срок добавится к уже оплаченному остатку. Нажимая кнопку ниже, "
        "ты принимаешь /terms.",
        reply_markup=inline(
            (("✅ Принимаю условия и оплачиваю", f"pay:confirm:{order.id}", "success"),),
            (("📄 Условия покупки", "pay:terms"),),
            (("💎 Другой тариф", "premium"), ("🏠 В меню", "home")),
        ),
    )


@router.callback_query(F.data == "premium:settings")
async def premium_settings(callback: CallbackQuery, store: Store, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    status = premium_status(user)
    if not status.is_premium:
        raise RuleError("Эта функция доступна только для Premium пользователей.")

    badge_status = "показывается" if user.show_premium_badge else "скрыт"

    await callback.message.answer(
        f"<b>⚙️ Настройки Premium</b>\n\n"
        f"Значок 💎: {badge_status}\n\n"
        "Значок показывается в твоей анкете, если настройка включена.",
        reply_markup=inline(
            (
                (
                    "Скрыть значок 💎" if user.show_premium_badge else "Показать значок 💎",
                    "premium:badge:toggle",
                ),
            ),
            (("💎 Premium", "premium"), ("🏠 В меню", "home")),
        ),
    )


@router.callback_query(F.data == "premium:badge:toggle")
async def toggle_badge(callback: CallbackQuery, store: Store, user: User) -> None:
    if not isinstance(callback.message, Message):
        return

    status = premium_status(user)
    if not status.is_premium:
        raise RuleError("Эта функция доступна только для Premium пользователей.")

    new_status = await store.toggle_premium_badge(user.id)
    await callback.message.answer(
        f"<b>Готово!</b> Значок 💎 {'показывается' if new_status else 'скрыт'} в твоей анкете.",
        reply_markup=menu(),
    )
