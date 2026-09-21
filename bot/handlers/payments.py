"""Telegram Stars purchase, support, reconciliation and refund handlers."""

import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramAPIError
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    LabeledPrice,
    Message,
    PreCheckoutQuery,
    TransactionPartnerUser,
)

from bot import texts
from bot.keyboards.common import inline
from bot.services.payments import (
    STARS_CURRENCY,
    PaymentInput,
    PaymentService,
    order_payload,
)
from bot.services.premium import PREMIUM_PLANS
from bot.services.store import Store
from bot.services.validation import RuleError

logger = logging.getLogger(__name__)
router = Router(name="payments")


def short_order(order_id: str) -> str:
    return order_id[:8].upper()


async def deliver_payment_notification(bot: Bot, service: PaymentService, order_id: str) -> bool:
    data = await service.notification_data(order_id)
    if not data:
        return False
    telegram_id, premium_until = data
    try:
        await bot.send_message(
            telegram_id,
            "<b>✅ Оплата получена — Premium активирован</b>\n\n"
            f"Заказ: <code>{short_order(order_id)}</code>\n"
            f"Доступ действует до: <b>{premium_until.strftime('%d.%m.%Y %H:%M UTC')}</b>\n\n"
            "Спасибо! Управлять Premium можно через кнопку 💎 Premium.",
        )
    except TelegramAPIError as exc:
        await service.mark_notification_error(order_id, type(exc).__name__)
        logger.warning("Не доставлено уведомление об оплате; заказ=%s", short_order(order_id))
        return False
    await service.mark_notification_sent(order_id)
    return True


@router.message(Command("terms"))
@router.callback_query(F.data == "pay:terms")
async def payment_terms(event: Message | CallbackQuery) -> None:
    message = event.message if isinstance(event, CallbackQuery) else event
    if isinstance(message, Message):
        await message.answer(texts.PAYMENT_TERMS)


@router.callback_query(F.data.startswith("pay:confirm:"))
async def confirm_invoice(callback: CallbackQuery, bot: Bot, store: Store) -> None:
    if not isinstance(callback.message, Message) or callback.data is None:
        return
    order_id = callback.data.removeprefix("pay:confirm:")
    service = PaymentService(store)
    order, action = await service.claim_invoice(order_id, callback.from_user.id)
    if action == "already_sent":
        await callback.message.answer("Счёт уже отправлен выше. Открой его и нажми кнопку оплаты.")
        return
    if action == "sending":
        await callback.message.answer("Счёт уже создаётся. Подожди несколько секунд.")
        return
    plan = PREMIUM_PLANS[order.plan_code]
    try:
        invoice = await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=f"Premium «Рядом»: {plan['label']}",
            description=(
                f"Разовая покупка Premium на {plan['label']}. Без автосписания и автопродления."
            ),
            payload=order_payload(order.id),
            provider_token="",
            currency=STARS_CURRENCY,
            prices=[LabeledPrice(label=f"Premium на {plan['label']}", amount=order.price_stars)],
            start_parameter=f"premium-{order.id[:16]}",
        )
    except TelegramAPIError as exc:
        await service.mark_invoice_error(order.id, type(exc).__name__)
        await callback.message.answer(
            "Не удалось отправить счёт. Покупка не состоялась, Stars не списаны. "
            "Попробуй нажать кнопку оплаты ещё раз."
        )
        return
    await service.mark_invoice_sent(order.id, invoice.message_id)


@router.pre_checkout_query()
async def pre_checkout(query: PreCheckoutQuery, store: Store) -> None:
    try:
        ok, error = await PaymentService(store).check_pre_checkout(
            query.from_user.id,
            query.invoice_payload,
            query.currency,
            query.total_amount,
        )
    except Exception:
        logger.exception("Ошибка короткой проверки платежа")
        ok, error = False, "Не удалось проверить заказ. Попробуй создать новый счёт."
    await query.answer(ok=ok, error_message=error)


@router.message(F.successful_payment)
async def successful_payment(message: Message, bot: Bot, store: Store) -> None:
    if message.from_user is None or message.successful_payment is None:
        return
    paid = message.successful_payment
    result = await PaymentService(store).complete_payment(
        PaymentInput(
            telegram_id=message.from_user.id,
            invoice_payload=paid.invoice_payload,
            currency=paid.currency,
            amount=paid.total_amount,
            charge_id=paid.telegram_payment_charge_id,
            provider_charge_id=paid.provider_payment_charge_id or None,
            paid_at=message.date,
            is_recurring=bool(paid.is_recurring),
        )
    )
    if result.status == "completed" and result.order_id:
        await deliver_payment_notification(bot, PaymentService(store), result.order_id)
    elif result.status == "review":
        await message.answer(
            "Платёж получен, но параметры требуют проверки. Premium не начислен автоматически. "
            "Отправь /paysupport — администратор увидит платёж."
        )


@router.message(F.refunded_payment)
async def refunded_payment(message: Message, store: Store) -> None:
    if message.from_user is None or message.refunded_payment is None:
        return
    refunded = message.refunded_payment
    result = await PaymentService(store).apply_refund(
        telegram_id=message.from_user.id,
        payload=refunded.invoice_payload,
        currency=refunded.currency,
        amount=refunded.total_amount,
        charge_id=refunded.telegram_payment_charge_id,
        refunded_at=message.date,
    )
    if result.status == "refunded":
        await message.answer(
            "<b>Возврат Stars учтён</b>\n\n"
            "Доступ по возвращённой покупке скорректирован. Другие покупки и "
            "административные выдачи сохранены."
        )


@router.message(Command("paysupport"))
async def payment_support(message: Message, bot: Bot, store: Store) -> None:
    if message.from_user is None:
        return
    parts = (message.text or "").split(maxsplit=1)
    requested = parts[1].strip().lower() if len(parts) == 2 else None
    order = await PaymentService(store).order_for_user(message.from_user.id)
    if requested and order and not order.id.startswith(requested):
        order = await PaymentService(store).order_for_user(message.from_user.id, requested)
    order_text = short_order(order.id) if order else "не найден"
    notice = (
        "<b>💳 Обращение по оплате</b>\n"
        f"Пользователь: <code>{message.from_user.id}</code>\n"
        f"Заказ: <code>{order_text}</code>\n"
        f"Статус: {order.status if order else 'нет заказа'}"
    )
    delivered = 0
    for admin_id in store.admin_ids:
        try:
            await bot.send_message(admin_id, notice)
            delivered += 1
        except TelegramAPIError:
            logger.warning("Не доставлено обращение одному из администраторов")
    if delivered:
        await message.answer(
            f"Обращение по заказу <code>{order_text}</code> передано администраторам. "
            "Они проверят оплату и при необходимости выполнят возврат Stars."
        )
    else:
        await message.answer(
            "Не удалось доставить обращение администраторам. Попробуй позже. "
            f"Сохрани номер заказа: <code>{order_text}</code>."
        )


@router.message(Command("payments"))
async def payment_orders(message: Message, store: Store) -> None:
    if message.from_user is None:
        return
    await show_order_page(message, store, message.from_user.id, 0)


async def show_order_page(message: Message, store: Store, admin_id: int, page: int) -> None:
    orders = await PaymentService(store).order_page(admin_id, page)
    rows = [
        (
            (
                f"{short_order(order.id)} · {order.price_stars}⭐ · {order.status}",
                f"payadmin:open:{order.id}",
            ),
        )
        for order in orders
    ]
    navigation = []
    if page:
        navigation.append(("← Назад", f"payadmin:list:{page - 1}"))
    if len(orders) == 5:
        navigation.append(("Далее →", f"payadmin:list:{page + 1}"))
    if navigation:
        rows.append(tuple(navigation))
    await message.answer(
        f"<b>💳 Заказы Premium</b>\nСтраница {page + 1}",
        reply_markup=inline(*rows),
    )


@router.callback_query(F.data.startswith("payadmin:"))
async def payment_admin_callback(callback: CallbackQuery, bot: Bot, store: Store) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    store.require_admin(callback.from_user.id)
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        raise RuleError("Недействительная кнопка платежа.")
    action, value = parts[1:]
    service = PaymentService(store)
    if action == "list":
        await show_order_page(callback.message, store, callback.from_user.id, int(value))
        return
    order, payment = await service.order_detail(callback.from_user.id, value)
    if action == "open":
        refund_button = ()
        if payment and payment.status == "completed":
            refund_button = (("Вернуть Stars", f"payadmin:refund:{order.id}", "danger"),)
        await callback.message.answer(
            "<b>💳 Заказ Premium</b>\n"
            f"Номер: <code>{short_order(order.id)}</code>\n"
            f"Пользователь: <code>{order.buyer_telegram_id}</code>\n"
            f"Тариф: {order.plan_code}\n"
            f"Сумма: {order.price_stars} {order.currency}\n"
            f"Статус заказа: {order.status}\n"
            f"Статус платежа: {payment.status if payment else 'нет'}",
            reply_markup=inline(
                refund_button,
                (("💳 К заказам", "payadmin:list:0"),),
            )
            if refund_button
            else inline((("💳 К заказам", "payadmin:list:0"),)),
        )
        return
    if action == "refund":
        if not payment or payment.status != "completed":
            raise RuleError("Этот платёж нельзя вернуть.")
        await callback.message.answer(
            "<b>Подтверди возврат</b>\n"
            f"Пользователь: <code>{order.buyer_telegram_id}</code>\n"
            f"Сумма: <b>{order.price_stars} ⭐️</b>\n"
            f"Заказ: <code>{short_order(order.id)}</code>",
            reply_markup=inline(
                (("Да, вернуть Stars", f"payadmin:confirmrefund:{order.id}", "danger"),),
                (("Отмена", f"payadmin:open:{order.id}"),),
            ),
        )
        return
    if action != "confirmrefund":
        raise RuleError("Недействительное действие с платежом.")
    payment = await service.mark_refund_pending(callback.from_user.id, order.id)
    try:
        refunded = await bot.refund_star_payment(
            user_id=order.buyer_telegram_id,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
        )
    except TelegramAPIError as exc:
        await service.mark_refund_unknown(payment.telegram_payment_charge_id, type(exc).__name__)
        await callback.message.answer(
            "Результат возврата неизвестен. Не повторяй его вслепую: запусти /stars_reconcile."
        )
        return
    if not refunded:
        await service.mark_refund_unknown(payment.telegram_payment_charge_id, "api_false")
        raise RuleError("Telegram не подтвердил возврат. Выполни сверку.")
    await service.apply_refund(
        telegram_id=order.buyer_telegram_id,
        payload=payment.invoice_payload,
        currency=payment.currency,
        amount=payment.amount,
        charge_id=payment.telegram_payment_charge_id,
    )
    await callback.message.answer(
        "<b>Возврат выполнен</b>\nStars возвращены, доступ скорректирован."
    )


@router.message(Command("stars_reconcile"))
async def reconcile_stars(message: Message, bot: Bot, store: Store) -> None:
    if message.from_user is None:
        return
    store.require_admin(message.from_user.id)
    service = PaymentService(store)
    incoming = refunded = skipped = 0
    offset = 0
    while True:
        page = await bot.get_star_transactions(offset=offset, limit=100)
        for transaction in page.transactions:
            partner = transaction.source
            if (
                isinstance(partner, TransactionPartnerUser)
                and partner.transaction_type == "invoice_payment"
                and partner.invoice_payload
            ):
                await service.complete_payment(
                    PaymentInput(
                        telegram_id=partner.user.id,
                        invoice_payload=partner.invoice_payload,
                        currency=STARS_CURRENCY,
                        amount=transaction.amount,
                        charge_id=transaction.id,
                        provider_charge_id=None,
                        paid_at=transaction.date,
                    )
                )
                incoming += 1
                continue
            partner = transaction.receiver
            if (
                isinstance(partner, TransactionPartnerUser)
                and partner.transaction_type == "invoice_payment"
                and partner.invoice_payload
            ):
                await service.apply_refund(
                    telegram_id=partner.user.id,
                    payload=partner.invoice_payload,
                    currency=STARS_CURRENCY,
                    amount=abs(transaction.amount),
                    charge_id=transaction.id,
                    refunded_at=transaction.date,
                )
                refunded += 1
                continue
            skipped += 1
        if len(page.transactions) < 100:
            break
        offset += 100
    for order in await service.pending_notifications():
        await deliver_payment_notification(bot, service, order.id)
    await message.answer(
        "<b>Сверка Stars завершена</b>\n"
        f"Входящие счета: {incoming}\nВозвраты: {refunded}\nПрочие операции: {skipped}"
    )