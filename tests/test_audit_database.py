"""Database audit regressions; all data uses the guarded PostgreSQL test fixture."""

import asyncio
from collections.abc import Awaitable
from datetime import UTC, datetime
from typing import Any

import pytest
from sqlalchemy import event, func, select

from bot.db.models import (
    BoostHistory,
    PremiumGrant,
    PremiumPayment,
    ProfilePhoto,
    Reaction,
    utcnow,
)
from bot.services.payments import PaymentInput, PaymentService, order_payload
from bot.services.premium import FREE_DAILY_LIKES
from bot.services.validation import RuleError


async def test_concurrent_likes_respect_shared_daily_budget(store, make_user):
    actor = await make_user()
    targets = [await make_user() for _ in range(FREE_DAILY_LIKES + 9)]
    async with store.db.sessions.begin() as session:
        session.add_all(
            Reaction(from_user_id=actor.id, to_user_id=target.id, kind="like")
            for target in targets[: FREE_DAILY_LIKES - 1]
        )

    results = await asyncio.gather(
        *(store.decide(actor.id, target.id, "like") for target in targets[FREE_DAILY_LIKES - 1 :]),
        return_exceptions=True,
    )
    unexpected = [
        result
        for result in results
        if isinstance(result, Exception) and not isinstance(result, RuleError)
    ]
    assert not unexpected
    assert (
        sum(
            getattr(result, "created", False)
            for result in results
            if not isinstance(result, BaseException)
        )
        == 1
    )
    assert await store.count_likes_today(actor.id) == FREE_DAILY_LIKES


async def test_duplicate_like_at_daily_limit_is_still_idempotent(store, make_user):
    actor = await make_user()
    targets = [await make_user() for _ in range(FREE_DAILY_LIKES)]
    async with store.db.sessions.begin() as session:
        session.add_all(
            Reaction(from_user_id=actor.id, to_user_id=target.id, kind="like") for target in targets
        )
    decision = await store.decide(actor.id, targets[0].id, "like")
    assert not decision.created
    assert await store.count_likes_today(actor.id) == FREE_DAILY_LIKES


async def test_concurrent_premium_grant_event_applies_once(store, make_user):
    actor = await make_user()
    results = await asyncio.gather(
        *(
            store.grant_premium(None, actor.id, "premium_3d", "audit-duplicate-grant")
            for _ in range(8)
        ),
        return_exceptions=True,
    )
    assert not [result for result in results if isinstance(result, Exception)]
    assert len(set(results)) == 1
    async with store.db.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(PremiumGrant)) == 1


async def test_concurrent_payment_replay_applies_once(store, make_user):
    actor = await make_user()
    service = PaymentService(store)
    order = await service.create_or_reuse_order(actor.id, actor.telegram_id, "premium_3d")
    paid_at = datetime.now(UTC)
    payment = PaymentInput(
        telegram_id=actor.telegram_id,
        invoice_payload=order_payload(order.id),
        currency="XTR",
        amount=order.price_stars,
        charge_id="audit-concurrent-charge",
        provider_charge_id=None,
        paid_at=paid_at,
    )
    results = await asyncio.gather(
        *(service.complete_payment(payment, now=paid_at) for _ in range(8)),
        return_exceptions=True,
    )
    assert not [result for result in results if isinstance(result, Exception)]
    assert {result.status for result in results} == {"completed"}
    async with store.db.sessions() as session:
        assert await session.scalar(select(func.count()).select_from(PremiumPayment)) == 1
        assert await session.scalar(select(func.count()).select_from(PremiumGrant)) == 1


async def test_primary_photo_is_unique_and_matches_profile(store, make_user):
    actor = await make_user()
    await store.grant_premium(None, actor.id, "premium_3d")
    added = await store.add_profile_photo(actor.id, "audit-secondary")
    await store.set_primary_photo(actor.id, added.id)
    photos = await store.get_profile_photos(actor.id)
    assert [photo.id for photo in photos if photo.is_primary] == [added.id]
    assert (await store.profile(actor.id)).photo_file_id == added.file_id


async def test_removing_primary_photo_updates_profile(store, make_user):
    actor = await make_user()
    await store.grant_premium(None, actor.id, "premium_3d")
    added = await store.add_profile_photo(actor.id, "audit-replacement")
    primary = next(photo for photo in await store.get_profile_photos(actor.id) if photo.is_primary)
    await store.remove_profile_photo(actor.id, primary.id)
    assert (await store.profile(actor.id)).photo_file_id == added.file_id
    assert [photo.id for photo in await store.get_profile_photos(actor.id) if photo.is_primary] == [
        added.id
    ]


async def test_editing_main_photo_updates_primary_gallery_row(store, make_user):
    actor = await make_user()
    await store.edit_profile(actor.id, "photo_file_id", "audit-edited-primary")
    profile, photos = await store.get_profile_with_photos(actor.id)
    assert profile is not None
    assert profile.photo_file_id == "audit-edited-primary"
    assert photos == ["audit-edited-primary"]


async def test_gallery_reuses_deleted_position(store, make_user):
    actor = await make_user()
    await store.grant_premium(None, actor.id, "premium_3d")
    added = [await store.add_profile_photo(actor.id, f"audit-photo-{i}") for i in range(4)]
    await store.remove_profile_photo(actor.id, added[1].id)
    replacement = await store.add_profile_photo(actor.id, "audit-reused-slot")
    assert replacement.position == added[1].position
    assert len(await store.get_profile_photos(actor.id)) == 5


async def test_concurrent_photo_add_respects_limit_without_database_error(store, make_user):
    actor = await make_user()
    await store.grant_premium(None, actor.id, "premium_3d")
    for index in range(3):
        await store.add_profile_photo(actor.id, f"audit-existing-{index}")
    results = await asyncio.gather(
        *(store.add_profile_photo(actor.id, f"audit-concurrent-{index}") for index in range(6)),
        return_exceptions=True,
    )
    assert sum(isinstance(result, ProfilePhoto) for result in results) == 1
    assert all(isinstance(result, (ProfilePhoto, RuleError)) for result in results)
    assert len(await store.get_profile_photos(actor.id)) == 5


async def test_concurrent_boost_activation_respects_cooldown(store, make_user):
    actor = await make_user()
    await store.grant_premium(None, actor.id, "premium_3d")
    now = utcnow()
    results = await asyncio.gather(
        *(store.activate_boost(actor.id, now) for _ in range(8)), return_exceptions=True
    )
    assert sum(isinstance(result, BoostHistory) for result in results) == 1
    assert all(isinstance(result, (BoostHistory, RuleError)) for result in results)


async def test_concurrent_free_undo_respects_daily_limit(store, make_user):
    actor, first, second = [await make_user() for _ in range(3)]
    await store.decide(actor.id, first.id, "pass")
    await store.decide(actor.id, second.id, "pass")
    results = await asyncio.gather(
        store.undo_last_pass(actor.id),
        store.undo_last_pass(actor.id),
        return_exceptions=True,
    )
    assert sum(not isinstance(result, Exception) for result in results) == 1
    assert sum(isinstance(result, RuleError) for result in results) == 1
    assert await store.count_undos_today(actor.id) == 1


async def test_named_flow_query_counts(store, make_user, capsys):
    """Record executed SQL statements without recording parameter values or user data."""
    actor, first, second, third = [await make_user() for _ in range(4)]
    counts: dict[str, int] = {}

    async def measure(name: str, operation: Awaitable[Any]) -> Any:
        queries = 0

        def count_query(*_args):
            nonlocal queries
            queries += 1

        event.listen(store.db.engine.sync_engine, "before_cursor_execute", count_query)
        try:
            return await operation
        finally:
            event.remove(store.db.engine.sync_engine, "before_cursor_execute", count_query)
            counts[name] = queries

    await measure("sync_existing_user", store.sync_user(actor.telegram_id, actor.username))
    await measure("profile", store.profile(actor.id))
    await measure("next_profile", store.next_profile(actor.id))
    await measure("profile_gallery", store.get_profile_with_photos(first.id))
    await measure("like_free", store.decide(actor.id, first.id, "like"))
    await measure("like_duplicate", store.decide(actor.id, first.id, "like"))
    await measure("pass", store.decide(actor.id, second.id, "pass"))
    await measure("like_reciprocal", store.decide(first.id, actor.id, "like"))
    await measure("match_page", store.match_page(actor.id, 0))
    await measure("admin_stats", store.stats(900_001))
    await measure("validate_known_target", store.validate_target(actor.id, first.id))
    await measure("block_unseen", store.block(actor.id, third.id))
    await store.grant_premium(None, actor.id, "premium_3d")
    fourth = await make_user()
    await measure("like_premium", store.decide(actor.id, fourth.id, "like"))
    with capsys.disabled():
        print(f"AUDIT_SQL_COUNTS {counts}")
    assert counts["profile"] == 1
    assert counts["match_page"] == 3
    assert len(await store.match_page(actor.id, 0)) == 1


@pytest.mark.parametrize("page", [-1, 1_000_001])
async def test_database_pagination_rejects_invalid_page(store, make_user, page):
    actor = await make_user()
    with pytest.raises(RuleError):
        await store.match_page(actor.id, page)
    with pytest.raises(RuleError):
        await store.report_page(900_001, page)
