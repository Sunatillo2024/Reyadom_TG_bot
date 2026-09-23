"""Persistent Telegram Stars orders, payment capture, reconciliation and refunds."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from secrets import token_hex

from sqlalchemy import func, select

from bot.db.models import PremiumGrant, PremiumOrder, PremiumPayment, User
from bot.services.premium import PREMIUM_PLANS
from bot.services.store import Store
from bot.services.validation import RuleError

STARS_CURRENCY = "XTR"
ORDER_TTL = timedelta(hours=1)
INVOICE_CLAIM_TTL = timedelta(minutes=2)
PAYLOAD_PREFIX = "premium_order:"

OPEN_ORDER_STATUSES = {
    "pending",
    "invoice_sending",
    "invoice_sent",
    "invoice_error",
    "checkout",
}


@dataclass(frozen=True)
class PaymentInput:
    telegram_id: int
    invoice_payload: str
    currency: str
    amount: int
    charge_id: str
    provider_charge_id: str | None
    paid_at: datetime
    is_recurring: bool = False


@dataclass(frozen=True)
class PaymentResult:
    status: str
    order_id: str | None
    premium_until: datetime | None = None


def order_payload(order_id: str) -> str:
    payload = f"{PAYLOAD_PREFIX}{order_id}"
    if len(payload.encode()) > 128:
        raise ValueError("Invoice payload exceeds Telegram limit")
    return payload


def payload_order_id(payload: str) -> str | None:
    if not payload.startswith(PAYLOAD_PREFIX):
        return None
    order_id = payload.removeprefix(PAYLOAD_PREFIX)
    if len(order_id) != 32 or any(char not in "0123456789abcdef" for char in order_id):
        return None
    return order_id


def plan_duration(plan_code: str) -> tuple[int, str]:
    plan = PREMIUM_PLANS.get(plan_code)
    if not plan:
        raise RuleError("Недействительный тариф Premium.")
    if "duration_days" in plan:
        return int(plan["duration_days"]), "days"
    return int(plan["duration_months"]), "months"


class PaymentService:
    def __init__(self, store: Store) -> None:
        self.store = store

    async def create_or_reuse_order(
        self,
        user_id: int,
        telegram_id: int,
        plan_code: str,
        *,
        now: datetime | None = None,
    ) -> PremiumOrder:
        if not self.store.stars_sales_enabled:
            raise RuleError("Новые покупки Premium временно приостановлены.")
        duration_value, duration_unit = plan_duration(plan_code)
        now = now or datetime.now(UTC)
        async with self.store.db.sessions.begin() as session:
            user = await session.scalar(select(User).where(User.id == user_id).with_for_update())
            if not user or user.telegram_id != telegram_id or user.is_banned:
                raise RuleError("Покупка Premium сейчас недоступна.")
            existing = await session.scalar(
                select(PremiumOrder)
                .where(
                    PremiumOrder.user_id == user_id,
                    PremiumOrder.plan_code == plan_code,
                    PremiumOrder.status.in_(OPEN_ORDER_STATUSES),
                    PremiumOrder.expires_at > now,
                )
                .order_by(PremiumOrder.created_at.desc())
                .limit(1)
            )
            if existing:
                return existing
            plan = PREMIUM_PLANS[plan_code]
            order = PremiumOrder(
                id=token_hex(16),
                user_id=user_id,
                buyer_telegram_id=telegram_id,
                plan_code=plan_code,
                price_stars=int(plan["price_stars"]),
                currency=STARS_CURRENCY,
                duration_value=duration_value,
                duration_unit=duration_unit,
                status="pending",
                expires_at=now + ORDER_TTL,
                created_at=now,
                updated_at=now,
            )
            session.add(order)
            return order

    async def claim_invoice(self, order_id: str, telegram_id: int) -> tuple[PremiumOrder, str]:
        now = datetime.now(UTC)
        async with self.store.db.sessions.begin() as session:
            order = await session.scalar(
                select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
            )
            if not order or order.buyer_telegram_id != telegram_id:
                raise RuleError("Заказ не найден или принадлежит другому пользователю.")
            if order.status in {"completed", "refunded", "review"}:
                raise RuleError("Этот заказ уже закрыт. Выбери тариф заново.")
            if order.expires_at <= now:
                raise RuleError("Время ожидания заказа истекло. Выбери тариф заново.")
            if not self.store.stars_sales_enabled:
                raise RuleError("Новые покупки Premium временно приостановлены.")
            user = await session.get(User, order.user_id)
            if not user or user.is_banned:
                raise RuleError("Покупка Premium сейчас недоступна.")
            if order.status == "invoice_sent" and order.invoice_message_id:
                return order, "already_sent"
            if order.status == "invoice_sending" and order.updated_at > now - INVOICE_CLAIM_TTL:
                return order, "sending"
            order.terms_accepted_at = order.terms_accepted_at or now
            order.status = "invoice_sending"
            order.updated_at = now
            order.last_error = None
            return order, "send"

    async def mark_invoice_sent(self, order_id: str, message_id: int) -> None:
        async with self.store.db.sessions.begin() as session:
            order = await session.scalar(
                select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
            )
            if order and order.status not in {"completed", "refunded"}:
                order.status = "invoice_sent"
                order.invoice_message_id = message_id
                order.last_error = None

    async def mark_invoice_error(self, order_id: str, reason: str) -> None:
        async with self.store.db.sessions.begin() as session:
            order = await session.scalar(
                select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
            )
            if order and order.status == "invoice_sending":
                order.status = "invoice_error"
                order.last_error = reason[:255]

    async def check_pre_checkout(
        self, telegram_id: int, payload: str, currency: str, amount: int
    ) -> tuple[bool, str | None]:
        order_id = payload_order_id(payload)
        if not order_id:
            return False, "Неизвестный заказ. Создай новый счёт в разделе Premium."
        now = datetime.now(UTC)
        async with self.store.db.sessions.begin() as session:
            order = await session.scalar(
                select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
            )
            if not order:
                return False, "Заказ не найден. Создай новый счёт в разделе Premium."
            if order.buyer_telegram_id != telegram_id:
                return False, "Этот счёт создан для другого пользователя."
            if order.currency != currency or order.price_stars != amount:
                order.status = "review"
                order.last_error = "pre_checkout_amount_mismatch"
                return False, "Сумма счёта не совпала с заказом. Оплата остановлена."
            if order.status not in {"invoice_sent", "invoice_sending", "checkout"}:
                return False, "Заказ уже закрыт или ещё не готов к оплате."
            if order.terms_accepted_at is None:
                return False, "Сначала подтверди условия покупки в боте."
            if order.expires_at <= now:
                return False, "Время ожидания счёта истекло. Создай новый заказ."
            if not self.store.stars_sales_enabled:
                return False, "Новые покупки Premium временно приостановлены."
            user = await session.get(User, order.user_id)
            if not user or user.is_banned:
                return False, "Покупка Premium сейчас недоступна."
            order.status = "checkout"
            order.last_error = None
            return True, None

    async def complete_payment(
        self, payment: PaymentInput, *, now: datetime | None = None
    ) -> PaymentResult:
        order_id = payload_order_id(payment.invoice_payload)
        now = now or datetime.now(UTC)
        async with self.store.db.sessions.begin() as session:
            # Telegram may replay the same immutable charge concurrently.
            await session.execute(
                select(func.pg_advisory_xact_lock(func.hashtextextended(payment.charge_id, 0)))
            )
            existing = await session.scalar(
                select(PremiumPayment)
                .where(PremiumPayment.telegram_payment_charge_id == payment.charge_id)
                .with_for_update()
            )
            if existing:
                order = (
                    await session.get(PremiumOrder, existing.order_id)
                    if existing.order_id
                    else None
                )
                return PaymentResult(
                    existing.status,
                    existing.order_id,
                    order and await self._order_until(session, order.id),
                )

            order = None
            if order_id:
                order = await session.scalar(
                    select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
                )

            reason = self._payment_mismatch(order, payment)
            if order and not reason:
                prior = await session.scalar(
                    select(PremiumPayment)
                    .where(
                        PremiumPayment.order_id == order.id,
                        PremiumPayment.status.in_({"completed", "refunded"}),
                    )
                    .with_for_update()
                )
                if prior:
                    reason = "order_already_paid"
            if reason:
                record = self._payment_record(payment, order, "review", reason)
                session.add(record)
                if order and order.status != "refunded":
                    order.status = "review"
                    order.last_error = reason
                return PaymentResult("review", order_id)

            assert order is not None
            user = await session.scalar(
                select(User).where(User.id == order.user_id).with_for_update()
            )
            if not user:
                session.add(self._payment_record(payment, order, "review", "user_missing"))
                order.status = "review"
                order.last_error = "user_missing"
                return PaymentResult("review", order.id)

            record = self._payment_record(payment, order, "completed", None)
            session.add(record)
            await session.flush()
            new_until = await self.store.grant_premium_in_session(
                session,
                None,
                user.id,
                order.plan_code,
                event_id=f"stars:{payment.charge_id}",
                source="stars",
                order_id=order.id,
                now=now,
            )
            order.status = "completed"
            order.last_error = None
            order.updated_at = now
            return PaymentResult("completed", order.id, new_until)

    @staticmethod
    def _payment_mismatch(order: PremiumOrder | None, payment: PaymentInput) -> str | None:
        if order is None:
            return "unknown_order"
        if order.status == "refunded":
            return "order_already_refunded"
        if order.buyer_telegram_id != payment.telegram_id:
            return "wrong_owner"
        if order.currency != payment.currency:
            return "wrong_currency"
        if order.price_stars != payment.amount:
            return "wrong_amount"
        if payment.is_recurring:
            return "unexpected_recurring_payment"
        return None

    @staticmethod
    def _payment_record(
        payment: PaymentInput,
        order: PremiumOrder | None,
        status: str,
        reason: str | None,
    ) -> PremiumPayment:
        return PremiumPayment(
            order_id=order.id if order else None,
            user_id=order.user_id if order else None,
            buyer_telegram_id=payment.telegram_id,
            telegram_payment_charge_id=payment.charge_id,
            provider_payment_charge_id=payment.provider_charge_id,
            invoice_payload=payment.invoice_payload,
            currency=payment.currency,
            amount=payment.amount,
            status=status,
            failure_reason=reason,
            paid_at=payment.paid_at,
        )

    @staticmethod
    async def _order_until(session, order_id: str) -> datetime | None:
        return await session.scalar(
            select(PremiumGrant.new_until)
            .where(PremiumGrant.order_id == order_id, PremiumGrant.action == "grant")
            .order_by(PremiumGrant.id.desc())
            .limit(1)
        )

    async def pending_notifications(self, limit: int = 20) -> list[PremiumOrder]:
        async with self.store.db.sessions() as session:
            return list(
                await session.scalars(
                    select(PremiumOrder)
                    .where(
                        PremiumOrder.status == "completed",
                        PremiumOrder.notification_sent_at.is_(None),
                    )
                    .order_by(PremiumOrder.created_at)
                    .limit(limit)
                )
            )

    async def notification_data(self, order_id: str) -> tuple[int, datetime] | None:
        async with self.store.db.sessions() as session:
            order = await session.get(PremiumOrder, order_id)
            if not order or order.status != "completed":
                return None
            premium_until = await self._order_until(session, order_id)
            if not premium_until:
                return None
            return order.buyer_telegram_id, premium_until

    async def mark_notification_sent(self, order_id: str) -> None:
        async with self.store.db.sessions.begin() as session:
            order = await session.get(PremiumOrder, order_id)
            if order and order.notification_sent_at is None:
                order.notification_sent_at = datetime.now(UTC)
                order.last_error = None

    async def mark_notification_error(self, order_id: str, reason: str) -> None:
        async with self.store.db.sessions.begin() as session:
            order = await session.get(PremiumOrder, order_id)
            if order and order.notification_sent_at is None:
                order.last_error = reason[:255]

    async def order_for_user(
        self, telegram_id: int, order_id: str | None = None
    ) -> PremiumOrder | None:
        async with self.store.db.sessions() as session:
            query = select(PremiumOrder).where(PremiumOrder.buyer_telegram_id == telegram_id)
            if order_id:
                query = query.where(PremiumOrder.id == order_id)
            return await session.scalar(query.order_by(PremiumOrder.created_at.desc()).limit(1))

    async def order_detail(
        self, admin_id: int, order_id: str
    ) -> tuple[PremiumOrder, PremiumPayment | None]:
        self.store.require_admin(admin_id)
        async with self.store.db.sessions() as session:
            order = await session.get(PremiumOrder, order_id)
            if not order:
                raise RuleError("Заказ не найден.")
            payment = await session.scalar(
                select(PremiumPayment)
                .where(PremiumPayment.order_id == order_id)
                .order_by(PremiumPayment.id.desc())
                .limit(1)
            )
            return order, payment

    async def order_page(self, admin_id: int, page: int) -> list[PremiumOrder]:
        self.store.require_admin(admin_id)
        if not 0 <= page <= 100_000:
            raise RuleError("Недопустимая страница.")
        async with self.store.db.sessions() as session:
            return list(
                await session.scalars(
                    select(PremiumOrder)
                    .order_by(PremiumOrder.created_at.desc())
                    .offset(page * 5)
                    .limit(5)
                )
            )

    async def mark_refund_pending(self, admin_id: int, order_id: str) -> PremiumPayment:
        self.store.require_admin(admin_id)
        async with self.store.db.sessions.begin() as session:
            order = await session.scalar(
                select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
            )
            payment = await session.scalar(
                select(PremiumPayment)
                .where(PremiumPayment.order_id == order_id)
                .order_by(PremiumPayment.id.desc())
                .with_for_update()
            )
            if not order or not payment or payment.status != "completed":
                raise RuleError("Для этого заказа нет платежа, доступного к возврату.")
            order.status = "refund_pending"
            payment.status = "refund_pending"
            return payment

    async def mark_refund_unknown(self, charge_id: str, reason: str) -> None:
        async with self.store.db.sessions.begin() as session:
            payment = await session.scalar(
                select(PremiumPayment)
                .where(PremiumPayment.telegram_payment_charge_id == charge_id)
                .with_for_update()
            )
            if payment and payment.status == "refund_pending":
                payment.status = "refund_unknown"
                payment.failure_reason = reason[:255]
                if payment.order_id:
                    order = await session.get(PremiumOrder, payment.order_id)
                    if order:
                        order.status = "refund_unknown"
                        order.last_error = reason[:255]

    async def apply_refund(
        self,
        *,
        telegram_id: int,
        payload: str,
        currency: str,
        amount: int,
        charge_id: str,
        refunded_at: datetime | None = None,
    ) -> PaymentResult:
        now = refunded_at or datetime.now(UTC)
        order_id = payload_order_id(payload)
        async with self.store.db.sessions.begin() as session:
            await session.execute(
                select(func.pg_advisory_xact_lock(func.hashtextextended(charge_id, 0)))
            )
            payment = await session.scalar(
                select(PremiumPayment)
                .where(PremiumPayment.telegram_payment_charge_id == charge_id)
                .with_for_update()
            )
            order = None
            if order_id:
                order = await session.scalar(
                    select(PremiumOrder).where(PremiumOrder.id == order_id).with_for_update()
                )
            if payment and payment.status == "refunded":
                return PaymentResult("refunded", payment.order_id)
            if not order or order.buyer_telegram_id != telegram_id:
                if payment:
                    payment.status = "review"
                    payment.failure_reason = "refund_order_or_owner_mismatch"
                else:
                    session.add(
                        PremiumPayment(
                            order_id=order.id if order else None,
                            user_id=order.user_id if order else None,
                            buyer_telegram_id=telegram_id,
                            telegram_payment_charge_id=charge_id,
                            provider_payment_charge_id=None,
                            invoice_payload=payload,
                            currency=currency,
                            amount=amount,
                            status="review",
                            failure_reason="refund_order_or_owner_mismatch",
                            paid_at=now,
                            refunded_at=now,
                        )
                    )
                if order:
                    order.status = "review"
                return PaymentResult("review", order_id)
            if order.currency != currency or order.price_stars != amount:
                if payment:
                    payment.status = "review"
                    payment.failure_reason = "refund_amount_mismatch"
                order.status = "review"
                order.last_error = "refund_amount_mismatch"
                return PaymentResult("review", order.id)
            if payment is None:
                payment = PremiumPayment(
                    order_id=order.id,
                    user_id=order.user_id,
                    buyer_telegram_id=telegram_id,
                    telegram_payment_charge_id=charge_id,
                    provider_payment_charge_id=None,
                    invoice_payload=payload,
                    currency=currency,
                    amount=amount,
                    status="refunded",
                    failure_reason="refund_received_before_payment",
                    paid_at=now,
                    refunded_at=now,
                )
                session.add(payment)
            else:
                payment.status = "refunded"
                payment.refunded_at = now
                payment.failure_reason = None

            await self._reverse_order_grant(session, order, charge_id, now)
            order.status = "refunded"
            order.last_error = None
            return PaymentResult("refunded", order.id)

    async def _reverse_order_grant(
        self, session, order: PremiumOrder, charge_id: str, now: datetime
    ) -> None:
        grant = await session.scalar(
            select(PremiumGrant)
            .where(
                PremiumGrant.order_id == order.id,
                PremiumGrant.action == "grant",
                PremiumGrant.source == "stars",
            )
            .order_by(PremiumGrant.id.desc())
            .with_for_update()
        )
        if not grant or grant.reversed_at is not None:
            return
        latest_revoke = await session.scalar(
            select(PremiumGrant.id)
            .where(
                PremiumGrant.user_id == grant.user_id,
                PremiumGrant.action == "revoke",
                PremiumGrant.id > grant.id,
            )
            .limit(1)
        )
        user = await session.scalar(select(User).where(User.id == grant.user_id).with_for_update())
        previous_until = user.premium_until if user else None
        remaining = timedelta(0)
        if not latest_revoke and grant.starts_at and grant.ends_at:
            remaining = max(timedelta(0), grant.ends_at - max(now, grant.starts_at))
        if user and user.premium_until and remaining:
            user.premium_until = max(now, user.premium_until - remaining)
            later_grants = list(
                await session.scalars(
                    select(PremiumGrant)
                    .where(
                        PremiumGrant.user_id == grant.user_id,
                        PremiumGrant.action == "grant",
                        PremiumGrant.id > grant.id,
                        PremiumGrant.reversed_at.is_(None),
                    )
                    .order_by(PremiumGrant.id)
                    .with_for_update()
                )
            )
            for later in later_grants:
                if later.starts_at:
                    later.starts_at -= remaining
                if later.ends_at:
                    later.ends_at -= remaining
        grant.reversed_at = now
        session.add(
            PremiumGrant(
                user_id=grant.user_id,
                granted_by=None,
                action="refund",
                plan_code=grant.plan_code,
                event_id=f"refund:{charge_id}",
                source="stars",
                order_id=order.id,
                previous_until=previous_until,
                new_until=user.premium_until if user else previous_until,
                created_at=now,
            )
        )
