from datetime import UTC, datetime, timedelta

import pytest

from bot.db.models import User
from bot.services.premium import (
    BOOST_COOLDOWN_HOURS,
    BOOST_DURATION_MINUTES,
    FREE_DAILY_LIKES,
    FREE_PHOTO_LIMIT,
    PREMIUM_PHOTO_LIMIT,
    calculate_premium_end,
    can_send_like,
    has_premium,
    photo_limit,
    premium_status,
)
from bot.services.store import Store
from bot.services.validation import RuleError


def test_calculate_premium_end() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    # 3 days
    end_3d = calculate_premium_end(None, "premium_3d", now)
    assert end_3d == now + timedelta(days=3)

    # 1 month (calendar month)
    end_1m = calculate_premium_end(None, "premium_1m", now)
    assert end_1m == datetime(2026, 2, 15, 12, 0, 0, tzinfo=UTC)

    # 3 months
    end_3m = calculate_premium_end(None, "premium_3m", now)
    assert end_3m == datetime(2026, 4, 15, 12, 0, 0, tzinfo=UTC)

    # Stack on top of active subscription
    active_until = datetime(2026, 1, 20, 12, 0, 0, tzinfo=UTC)
    stacked = calculate_premium_end(active_until, "premium_3d", now)
    assert stacked == active_until + timedelta(days=3)

    # Stack when expired (should use now)
    expired_until = datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC)
    from_expired = calculate_premium_end(expired_until, "premium_3d", now)
    assert from_expired == now + timedelta(days=3)


def test_has_premium() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Free user
    user_free = User(id=1, telegram_id=1, premium_until=None)
    assert not has_premium(user_free, now)

    # Active premium
    user_prem = User(id=2, telegram_id=2, premium_until=datetime(2026, 1, 20, 12, 0, 0, tzinfo=UTC))
    assert has_premium(user_prem, now)

    # Expired premium
    user_exp = User(id=3, telegram_id=3, premium_until=datetime(2026, 1, 10, 12, 0, 0, tzinfo=UTC))
    assert not has_premium(user_exp, now)


def test_photo_limit() -> None:
    user_free = User(id=1, telegram_id=1, premium_until=None)
    user_prem = User(id=2, telegram_id=2, premium_until=datetime.now(UTC) + timedelta(days=30))

    assert photo_limit(user_free) == FREE_PHOTO_LIMIT
    assert photo_limit(user_prem) == PREMIUM_PHOTO_LIMIT


def test_can_send_like() -> None:
    user_free = User(id=1, telegram_id=1, premium_until=None)
    user_prem = User(id=2, telegram_id=2, premium_until=datetime.now(UTC) + timedelta(days=30))

    # Free user within limits
    allowed, _ = can_send_like(user_free, 0)
    assert allowed
    allowed, _ = can_send_like(user_free, 10)
    assert allowed

    # Free user exceeds limits
    allowed, err = can_send_like(user_free, FREE_DAILY_LIKES)
    assert not allowed
    assert "лимит" in err.lower()

    # Premium user has no limits
    allowed, _ = can_send_like(user_prem, 0)
    assert allowed
    allowed, _ = can_send_like(user_prem, 100)
    assert allowed


def test_premium_status() -> None:
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    user_free = User(id=1, telegram_id=1, premium_until=None)
    status_free = premium_status(user_free, now)
    assert not status_free.is_premium
    assert status_free.days_left == 0
    assert status_free.until is None

    user_prem = User(id=2, telegram_id=2, premium_until=datetime(2026, 1, 20, 12, 0, 0, tzinfo=UTC))
    status_prem = premium_status(user_prem, now)
    assert status_prem.is_premium
    assert status_prem.days_left == 5
    assert status_prem.until is not None


@pytest.mark.asyncio
async def test_grant_and_revoke_premium(store: Store) -> None:
    admin_user = await store.sync_user(999999, "admin")
    target_user = await store.sync_user(123456, "target")

    # Grant 3 days
    new_until = await store.grant_premium(admin_user.id, target_user.id, "premium_3d")
    assert new_until is not None

    user = await store.sync_user(123456, "target")
    assert user.premium_until is not None
    assert has_premium(user)

    # Revoke
    await store.revoke_premium(admin_user.id, target_user.id)
    user = await store.sync_user(123456, "target")
    assert user.premium_until is None
    assert not has_premium(user)


@pytest.mark.asyncio
async def test_toggle_premium_badge(store: Store) -> None:
    user = await store.sync_user(123456, "testuser")
    assert user.show_premium_badge is True

    # Toggle off
    new_val = await store.toggle_premium_badge(user.id)
    assert new_val is False

    # Toggle on
    new_val = await store.toggle_premium_badge(user.id)
    assert new_val is True


@pytest.mark.asyncio
async def test_undo_last_pass(store: Store) -> None:
    u1 = await store.sync_user(1001, "u1")
    u2 = await store.sync_user(1002, "u2")

    await store.save_profile(
        u1.id,
        {
            "name": "User 1",
            "age": 25,
            "gender": "male",
            "seeking": "female",
            "city": "Ташкент",
            "bio": "Bio 1",
            "photo_file_id": "photo1",
            "consent_at": datetime.now(UTC),
        },
    )

    await store.save_profile(
        u2.id,
        {
            "name": "User 2",
            "age": 23,
            "gender": "female",
            "seeking": "male",
            "city": "Ташкент",
            "bio": "Bio 2",
            "photo_file_id": "photo2",
            "consent_at": datetime.now(UTC),
        },
    )

    # U1 passes on U2
    dec = await store.decide(u1.id, u2.id, "pass")
    assert dec.created is True

    # Undo pass
    unpassed = await store.undo_last_pass(u1.id)
    assert unpassed is not None
    assert unpassed.user_id == u2.id

    # Try undo again (should be None)
    unpassed_again = await store.undo_last_pass(u1.id)
    assert unpassed_again is None


@pytest.mark.asyncio
async def test_profile_photo_limits(store: Store) -> None:
    user = await store.sync_user(2001, "photos_user")

    await store.save_profile(
        user.id,
        {
            "name": "Photo User",
            "age": 25,
            "gender": "male",
            "seeking": "female",
            "city": "Ташкент",
            "bio": "Bio",
            "photo_file_id": "photo_1",
            "consent_at": datetime.now(UTC),
        },
    )

    # Free user has 1 photo already from profile creation, adding another should fail
    with pytest.raises(RuleError, match="лимит фото"):
        await store.add_profile_photo(user.id, "photo_2")

    # Grant Premium
    admin = await store.sync_user(999999, "admin")
    await store.grant_premium(admin.id, user.id, "premium_1m")

    # Now can add up to 5 photos total (already has 1)
    await store.add_profile_photo(user.id, "photo_2")
    await store.add_profile_photo(user.id, "photo_3")
    await store.add_profile_photo(user.id, "photo_4")
    p5 = await store.add_profile_photo(user.id, "photo_5")

    photos = await store.get_profile_photos(user.id)
    assert len(photos) == 5

    # 6th photo should fail
    with pytest.raises(RuleError, match="лимит фото"):
        await store.add_profile_photo(user.id, "photo_6")

    # Can remove a photo
    await store.remove_profile_photo(user.id, p5.id)
    photos = await store.get_profile_photos(user.id)
    assert len(photos) == 4


@pytest.mark.asyncio
async def test_boost_activation_and_cooldown(store: Store) -> None:
    user = await store.sync_user(3001, "boost_user")
    now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=UTC)

    # Free user cannot boost
    with pytest.raises(RuleError, match="Premium"):
        await store.activate_boost(user.id, now)

    # Grant Premium
    admin = await store.sync_user(999999, "admin")
    await store.grant_premium(admin.id, user.id, "premium_1m")

    # Activate boost
    boost = await store.activate_boost(user.id, now)
    assert boost.user_id == user.id
    assert boost.ends_at == now + timedelta(minutes=BOOST_DURATION_MINUTES)
    assert boost.next_available_at == now + timedelta(hours=BOOST_COOLDOWN_HOURS)

    # Cannot activate again immediately
    with pytest.raises(RuleError, match="через"):
        await store.activate_boost(user.id, now + timedelta(minutes=10))

    # Can activate after cooldown
    after_cooldown = now + timedelta(hours=BOOST_COOLDOWN_HOURS + 1)
    boost2 = await store.activate_boost(user.id, after_cooldown)
    assert boost2.id != boost.id
