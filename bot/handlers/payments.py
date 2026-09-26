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

from bot.i18n import tr
from bot.keyboards.common import inline
from bot.services.payments import (
    STARS_CURRENCY,
    PaymentInput,
    PaymentService,
    order_payload,
)
from bot.services.premium import plan_label
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
    language = await service.store.language_of(telegram_id)
    try:
        await bot.send_message(
            telegram_id,
            tr(
                "payment_success",
                language,
                order=short_order(order_id),
                until=premium_until.strftime("%d.%m.%Y %H:%M UTC"),
            ),
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
        await message.answer(tr("payment_terms"))


@router.callback_query(F.data.startswith("pay:confirm:"))
async def confirm_invoice(callback: CallbackQuery, bot: Bot, store: Store) -> None:
    if not isinstance(callback.message, Message) or callback.data is None:
        return
    order_id = callback.data.removeprefix("pay:confirm:")
    service = PaymentService(store)
    order, action = await service.claim_invoice(order_id, callback.from_user.id)
    if action == "already_sent":
        await callback.message.answer(tr("invoice_already_sent"))
        return
    if action == "sending":
        await callback.message.answer(tr("invoice_sending"))
        return
    label = plan_label(order.plan_code)
    try:
        invoice = await bot.send_invoice(
            chat_id=callback.from_user.id,
            title=tr("invoice_title", plan=label),
            description=tr("invoice_description", plan=label),
            payload=order_payload(order.id),
            provider_token="",
            currency=STARS_CURRENCY,
            prices=[LabeledPrice(label=tr("invoice_label", plan=label), amount=order.price_stars)],
            start_parameter=f"premium-{order.id[:16]}",
        )
    except TelegramAPIError as exc:
        await service.mark_invoice_error(order.id, type(exc).__name__)
        await callback.message.answer(tr("invoice_error"))
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
        ok, error = False, tr("err_checkout_failed")
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
        await message.answer(tr("payment_review"))


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
        await message.answer(tr("refund_ack"))


@router.message(Command("paysupport"))
async def payment_support(message: Message, bot: Bot, store: Store) -> None:
    if message.from_user is None:
        return
    parts = (message.text or "").split(maxsplit=1)
    requested = parts[1].strip().lower() if len(parts) == 2 else None
    order = await PaymentService(store).order_for_user(message.from_user.id)
    if requested and order and not order.id.startswith(requested):
        order = await PaymentService(store).order_for_user(message.from_user.id, requested)
    order_text = short_order(order.id) if order else tr("paysupport_none")
    status_text = order.status if order else tr("paysupport_no_order")
    delivered = 0
    for admin_id in store.admin_ids:
        language = await store.language_of(admin_id)
        notice = tr(
            "paysupport_admin",
            language,
            telegram_id=message.from_user.id,
            order=order_text,
            status=status_text,
        )
        try:
            await bot.send_message(admin_id, notice)
            delivered += 1
        except TelegramAPIError:
            logger.warning("Не доставлено обращение одному из администраторов")
    if delivered:
        await message.answer(tr("paysupport_sent", order=order_text))
    else:
        await message.answer(tr("paysupport_failed", order=order_text))


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
        navigation.append((tr("matches_prev"), f"payadmin:list:{page - 1}"))
    if len(orders) == 5:
        navigation.append((tr("matches_next"), f"payadmin:list:{page + 1}"))
    if navigation:
        rows.append(tuple(navigation))
    await message.answer(
        tr("payadmin_title", page=page + 1),
        reply_markup=inline(*rows),
    )


@router.callback_query(F.data.startswith("payadmin:"))
async def payment_admin_callback(callback: CallbackQuery, bot: Bot, store: Store) -> None:
    if callback.data is None or not isinstance(callback.message, Message):
        return
    store.require_admin(callback.from_user.id)
    parts = callback.data.split(":", 2)
    if len(parts) != 3:
        raise RuleError(tr("err_invalid_payment_button"))
    action, value = parts[1:]
    service = PaymentService(store)
    if action == "list":
        await show_order_page(callback.message, store, callback.from_user.id, int(value))
        return
    order, payment = await service.order_detail(callback.from_user.id, value)
    if action == "open":
        refund_button = ()
        if payment and payment.status == "completed":
            refund_button = ((tr("refund_button"), f"payadmin:refund:{order.id}", "danger"),)
        await callback.message.answer(
            tr(
                "payadmin_order",
                order=short_order(order.id),
                buyer=order.buyer_telegram_id,
                plan=order.plan_code,
                price=order.price_stars,
                currency=order.currency,
                status=order.status,
                payment_status=payment.status if payment else tr("payadmin_no_payment"),
            ),
            reply_markup=inline(
                refund_button,
                ((tr("payadmin_back"), "payadmin:list:0"),),
            )
            if refund_button
            else inline(((tr("payadmin_back"), "payadmin:list:0"),)),
        )
        return
    if action == "refund":
        if not payment or payment.status != "completed":
            raise RuleError(tr("err_no_refundable_payment"))
        await callback.message.answer(
            tr(
                "refund_confirm_prompt",
                buyer=order.buyer_telegram_id,
                price=order.price_stars,
                order=short_order(order.id),
            ),
            reply_markup=inline(
                ((tr("refund_yes"), f"payadmin:confirmrefund:{order.id}", "danger"),),
                ((tr("delete_cancel"), f"payadmin:open:{order.id}"),),
            ),
        )
        return
    if action != "confirmrefund":
        raise RuleError(tr("err_invalid_payment_action"))
    payment = await service.mark_refund_pending(callback.from_user.id, order.id)
    try:
        refunded = await bot.refund_star_payment(
            user_id=order.buyer_telegram_id,
            telegram_payment_charge_id=payment.telegram_payment_charge_id,
        )
    except TelegramAPIError as exc:
        await service.mark_refund_unknown(payment.telegram_payment_charge_id, type(exc).__name__)
        await callback.message.answer(tr("refund_unknown"))
        return
    if not refunded:
        await service.mark_refund_unknown(payment.telegram_payment_charge_id, "api_false")
        raise RuleError(tr("err_refund_not_confirmed"))
    await service.apply_refund(
        telegram_id=order.buyer_telegram_id,
        payload=payment.invoice_payload,
        currency=payment.currency,
        amount=payment.amount,
        charge_id=payment.telegram_payment_charge_id,
    )
    await callback.message.answer(tr("refund_done"))


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
        tr("reconcile_done", incoming=incoming, refunded=refunded, skipped=skipped)
    )
