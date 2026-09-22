import asyncio
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select

from bot.db.models import PremiumGrant, PremiumPayment, User
from bot.services.payments import PaymentInput, PaymentService, order_payload
from bot.services.premium import get_effective_premium_until, has_premium, premium_status
from bot.services.store import Store
from bot.services.welcome_trial import notification_text


def enabled_store(store: Store) -> Store:
    return Store(
        store.db,
        list(store.admin_ids),
        welcome_trial_enabled=True,
        welcome_trial_days=7,
    )


async def test_new_user_gets_exactly_one_trial_and_restart_does_not_extend(store):
    trial_store = enabled_store(store)
    started_at = datetime(2026, 9, 22, 8, 30, tzinfo=UTC)

    first = await trial_store.sync_user_with_status(700_001, "new_user", now=started_at)
    second = await trial_store.sync_user_with_status(
        700_001, "new_user", now=started_at + timedelta(days=1)
    )
    await trial_store.delete_profile(first.user.id)
    recreated = await trial_store.sync_user_with_status(
        700_001, "new_user", now=started_at + timedelta(days=2)
    )

    assert first.welcome_trial_granted
    assert not second.welcome_trial_granted
    assert not recreated.welcome_trial_granted
    assert first.user.trial_used
    assert recreated.user.trial_started_at == started_at
    assert recreated.user.trial_ends_at == started_at + timedelta(days=7)
    assert recreated.user.trial_ends_at is not None
    assert recreated.user.trial_ends_at.utcoffset() == timedelta(0)
    async with store.db.sessions() as session:
        assert await session.scalar(
            select(func.count()).select_from(User).where(User.telegram_id == 700_001)
        ) == 1


async def test_parallel_registration_creates_one_user_and_one_trial(store):
    trial_store = enabled_store(store)
    started_at = datetime(2026, 9, 22, 9, 0, tzinfo=UTC)

    results = await asyncio.gather(
        *(
            trial_store.sync_user_with_status(700_002, "parallel", now=started_at)
            for _ in range(8)
        )
    )

    assert sum(result.welcome_trial_granted for result in results) == 1
    assert {result.user.id for result in results} == {results[0].user.id}
    assert {result.user.trial_ends_at for result in results} == {
        started_at + timedelta(days=7)
    }
    async with store.db.sessions() as session:
        assert await session.scalar(
            select(func.count()).select_from(User).where(User.telegram_id == 700_002)
        ) == 1


def test_effective_premium_uses_later_end_and_trial_expires_exactly_at_boundary():
    now = datetime(2026, 9, 22, 10, 0, tzinfo=UTC)
    user = User(
        id=1,
        telegram_id=1,
        trial_used=True,
        trial_started_at=now,
        trial_ends_at=now + timedelta(days=7),
        premium_until=now + timedelta(days=3),
    )

    assert get_effective_premium_until(user) == now + timedelta(days=7)
    assert has_premium(user, now + timedelta(days=7) - timedelta(microseconds=1))
    assert not has_premium(user, now + timedelta(days=7))
    assert premium_status(user, now).kind == "trial"

    user.premium_until = now + timedelta(days=10)
    assert get_effective_premium_until(user) == now + timedelta(days=10)
    assert premium_status(user, now).kind == "paid"


async def test_purchase_during_trial_stacks_and_payment_retry_is_idempotent(store):
    trial_store = enabled_store(store)
    service = PaymentService(trial_store)
    now = datetime(2026, 9, 22, 11, 0, tzinfo=UTC)
    user = await trial_store.sync_user(700_003, "buyer", now=now)
    order = await service.create_or_reuse_order(
        user.id, user.telegram_id, "premium_3d", now=now
    )
    payment = PaymentInput(
        telegram_id=user.telegram_id,
        invoice_payload=order_payload(order.id),
        currency="XTR",
        amount=order.price_stars,
        charge_id="welcome-trial-payment-1",
        provider_charge_id=None,
        paid_at=now,
    )

    first = await service.complete_payment(payment, now=now)
    retry = await service.complete_payment(payment, now=now + timedelta(minutes=1))

    expected_until = now + timedelta(days=10)
    assert first.premium_until == expected_until
    assert retry.premium_until == expected_until
    refreshed = await trial_store.sync_user(user.telegram_id, user.username, now=now)
    assert refreshed.premium_until == expected_until
    async with store.db.sessions() as session:
        assert await session.scalar(
            select(func.count())
            .select_from(PremiumPayment)
            .where(PremiumPayment.telegram_payment_charge_id == payment.charge_id)
        ) == 1
        assert await session.scalar(
            select(func.count())
            .select_from(PremiumGrant)
            .where(PremiumGrant.event_id == f"stars:{payment.charge_id}")
        ) == 1


async def test_disabled_trial_is_consumed_without_grant(store):
    disabled_store = Store(
        store.db,
        list(store.admin_ids),
        welcome_trial_enabled=False,
        welcome_trial_days=7,
    )
    enabled_later = enabled_store(store)
    now = datetime(2026, 9, 22, 12, 0, tzinfo=UTC)

    first = await disabled_store.sync_user_with_status(700_004, "disabled", now=now)
    later = await enabled_later.sync_user_with_status(
        700_004, "disabled", now=now + timedelta(days=1)
    )

    assert first.user.trial_used
    assert first.user.trial_started_at is None
    assert first.user.trial_ends_at is None
    assert not first.welcome_trial_granted
    assert not later.welcome_trial_granted
    assert later.user.trial_ends_at is None


async def test_trial_notifications_are_claimed_only_once(store):
    trial_store = enabled_store(store)
    started_at = datetime(2026, 9, 22, 13, 0, tzinfo=UTC)
    user = await trial_store.sync_user(700_005, "notices", now=started_at)

    welcome = await trial_store.claim_trial_notifications(now=started_at, user_id=user.id)
    assert [item.kind for item in welcome] == ["welcome"]
    assert "Premium бесплатно на 7 дней" in notification_text(welcome[0])
    assert await trial_store.claim_trial_notifications(now=started_at, user_id=user.id) == []

    reminder_at = started_at + timedelta(days=6, hours=1)
    reminder = await trial_store.claim_trial_notifications(now=reminder_at, user_id=user.id)
    assert [item.kind for item in reminder] == ["reminder"]
    assert await trial_store.claim_trial_notifications(now=reminder_at, user_id=user.id) == []

    expired_at = started_at + timedelta(days=7)
    expired = await trial_store.claim_trial_notifications(now=expired_at, user_id=user.id)
    assert [item.kind for item in expired] == ["expired"]
    assert await trial_store.claim_trial_notifications(now=expired_at, user_id=user.id) == []
