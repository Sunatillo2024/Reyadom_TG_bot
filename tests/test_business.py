import asyncio
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramServerError,
)
from aiogram.methods import GetChat, SendMessage
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from bot.db.database import Database
from bot.db.models import Block, Match, Profile, Reaction, Report, User, utcnow
from bot.keyboards.common import decisions, inline, menu
from bot.services.store import Store
from bot.services.telegram import caption, contact_url, notify_decision
from bot.services.validation import RuleError, age_range, age_value, clean_text, normalize_city
from bot.texts import LEGACY_MENU_LABELS, MENU_LABEL_ALIASES, MENU_LABELS, PREVIOUS_MENU_LABELS


async def count_rows(store, model):
    async with store.db.sessions() as session:
        return await session.scalar(select(func.count()).select_from(model))


@pytest.mark.parametrize("value", [17, 100, "18.5", "abc", True, "-20", "１８"])
def test_invalid_age(value):
    with pytest.raises(RuleError):
        age_value(value)


@pytest.mark.parametrize("limits", [(17, 40), (40, 39), (18, 100)])
def test_invalid_age_range(limits):
    with pytest.raises(RuleError):
        age_range(*limits)


@pytest.mark.parametrize(
    "value",
    [
        "Salom @somebody",
        "t.me/person",
        "telegram.me/user",
        "https://example.org",
        "www.example.uz",
        "example.com/path",
        "tg://user?id=1",
    ],
)
def test_no_public_contact(value):
    with pytest.raises(RuleError):
        clean_text(value, 0, 300)


def test_city_and_html():
    assert normalize_city("  New   YORK  ") == "new york"
    assert normalize_city("Toshkent") != normalize_city("Ташкент")
    profile = Profile(name="<Ali>", age=25, city="A&B", bio="<b>Salom</b>")
    assert caption(profile) == "<b>&lt;Ali&gt;, 25</b>\n📍 A&amp;B\n\n&lt;b&gt;Salom&lt;/b&gt;"


def test_ui_labels_callbacks_and_button_styles_are_serialized():
    markup = menu()
    assert [[button.text for button in row] for row in markup.keyboard] == [
        [MENU_LABELS[0]],
        [MENU_LABELS[1], MENU_LABELS[2]],
        [MENU_LABELS[3]],
        [MENU_LABELS[4], MENU_LABELS[5]],
        [MENU_LABELS[6]],
    ]
    assert markup.input_field_placeholder == "Выбери действие 💜"
    serialized_menu = markup.model_dump(exclude_none=True)
    assert serialized_menu["keyboard"][0][0]["style"] == "primary"
    serialized_request = SendMessage(chat_id=1, text="Меню", reply_markup=markup).model_dump(
        exclude_none=True
    )
    assert serialized_request["reply_markup"]["keyboard"][0][0]["style"] == "primary"
    assert all("style" not in button for row in serialized_menu["keyboard"][1:] for button in row)

    styled = inline((("Сохранить", "save", "success"),))
    assert styled.model_dump(exclude_none=True)["inline_keyboard"][0][0]["style"] == "success"
    decision_data = [
        button.callback_data for row in decisions(42).inline_keyboard for button in row
    ]
    assert decision_data == [
        "react:42:like:d",
        "react:42:pass:d",
        "undo:pass",
        "block:42",
        "report:42",
        "home",
    ]

    for index in range(len(MENU_LABELS)):
        assert MENU_LABELS[index] in MENU_LABEL_ALIASES[index]
        assert PREVIOUS_MENU_LABELS[index] in MENU_LABEL_ALIASES[index]
        assert LEGACY_MENU_LABELS[index] in MENU_LABEL_ALIASES[index]


async def test_unconfirmed_and_database_constraints(store, make_user):
    a = await make_user()
    b = await make_user(confirmed=False)
    assert await store.next_profile(a.id) is None
    with pytest.raises(RuleError):
        await store.decide(a.id, b.id, "like")
    with pytest.raises(IntegrityError):
        async with store.db.sessions.begin() as session:
            profile = await session.get(Profile, a.id)
            profile.age = 17
    with pytest.raises(IntegrityError):
        async with store.db.sessions.begin() as session:
            profile = await session.get(Profile, a.id)
            profile.min_age, profile.max_age = 50, 20
    with pytest.raises(IntegrityError):
        async with store.db.sessions.begin() as session:
            session.add(Reaction(from_user_id=a.id, to_user_id=99999, kind="like"))


async def test_reciprocal_filters(store, make_user):
    a = await make_user(gender="male", seeking="female", age=30, city="New  York")
    b = await make_user(gender="female", seeking="male", age=26, city="new york")
    assert (await store.next_profile(a.id)).user_id == b.id

    await store.settings(b.id, 18, 29, True)
    assert await store.next_profile(a.id) is None
    await store.settings(b.id, 18, 99, True)
    await store.settings(a.id, 27, 99, True)
    assert await store.next_profile(a.id) is None
    await store.settings(a.id, 18, 99, True)
    await store.edit_profile(b.id, "seeking", "female")
    assert await store.next_profile(a.id) is None
    await store.edit_profile(b.id, "seeking", "male")
    await store.edit_profile(b.id, "gender", "male")
    assert await store.next_profile(a.id) is None
    await store.edit_profile(b.id, "gender", "female")
    await store.edit_profile(b.id, "city", "Bishkek")
    await store.settings(a.id, 18, 99, False)
    assert await store.next_profile(a.id) is None  # B still requires own city.
    await store.settings(b.id, 18, 99, False)
    assert (await store.next_profile(a.id)).user_id == b.id


async def test_location_candidates_are_sorted_from_nearest_to_farthest(store, make_user):
    actor = await make_user(gender="male", seeking="female", latitude=42.8746, longitude=74.5698)
    farther = await make_user(gender="female", seeking="male", latitude=42.9500, longitude=74.7000)
    nearest = await make_user(gender="female", seeking="male", latitude=42.8760, longitude=74.5710)

    candidate = await store.next_profile(actor.id)
    assert candidate.user_id == nearest.id
    assert candidate.distance_km is not None and candidate.distance_km < 1

    await store.decide(actor.id, nearest.id, "pass")
    candidate = await store.next_profile(actor.id)
    assert candidate.user_id == farther.id
    assert candidate.distance_km is not None and candidate.distance_km > 1


@pytest.mark.parametrize(
    "exclude",
    [
        "hidden",
        "banned",
        "block_forward",
        "block_reverse",
        "pass_forward",
        "pass_reverse",
        "deleted",
        "username",
    ],
)
async def test_exclusions_in_both_directions(store, make_user, exclude):
    a, b = await make_user(), await make_user()
    if exclude == "hidden":
        await store.set_active(b.id, False)
    elif exclude == "banned":
        await store.ban_by_telegram(900_001, b.telegram_id, True)
    elif exclude == "block_forward":
        await store.block(a.id, b.id)
    elif exclude == "block_reverse":
        await store.block(b.id, a.id)
    elif exclude == "pass_forward":
        await store.decide(a.id, b.id, "pass")
    elif exclude == "pass_reverse":
        await store.decide(b.id, a.id, "pass")
    elif exclude == "deleted":
        await store.delete_profile(b.id)
    else:
        await store.sync_user(b.telegram_id, None)
    assert await store.next_profile(a.id) is None
    with pytest.raises(RuleError):
        await store.decide(a.id, a.id, "like")


async def test_incoming_revalidated_and_hidden_cannot_send(store, make_user):
    a, b = await make_user(), await make_user()
    await store.decide(a.id, b.id, "like")
    assert (await store.next_profile(b.id, incoming=True)).user_id == a.id
    await store.settings(a.id, 40, 50, True)
    assert await store.next_profile(b.id, incoming=True) is None
    await store.settings(a.id, 18, 99, True)
    await store.set_active(a.id, False)
    assert await store.next_profile(b.id, incoming=True) is None
    with pytest.raises(RuleError):
        await store.decide(a.id, b.id, "like")
    await store.set_active(a.id, True)
    await store.decide(b.id, a.id, "pass")
    assert await store.next_profile(b.id, incoming=True) is None


async def test_like_match_idempotence_and_notifications(store, make_user):
    a, b = await make_user(), await make_user()
    first = await store.decide(a.id, b.id, "like")
    assert first.created and first.match_id is None
    assert await count_rows(store, Match) == 0
    second = await store.decide(b.id, a.id, "like")
    assert second.created and second.match_id
    bot = SimpleNamespace(send_message=AsyncMock())
    await notify_decision(bot, store, a.telegram_id, first, "like")
    await notify_decision(bot, store, b.telegram_id, second, "like")
    repeated = await store.decide(b.id, a.id, "pass")
    await notify_decision(bot, store, b.telegram_id, repeated, "pass")
    assert not repeated.created
    assert bot.send_message.await_count == 3  # one like, two match notifications
    assert await count_rows(store, Reaction) == 2
    assert await count_rows(store, Match) == 1
    assert await store.next_profile(a.id) is None
    assert await store.next_profile(b.id, incoming=True) is None


async def test_concurrent_reciprocal_likes(store, make_user):
    a, b = await make_user(), await make_user()
    requests = [(a, b), (b, a)] * 8
    results = await asyncio.gather(*(store.decide(x.id, y.id, "like") for x, y in requests))
    assert sum(result.created for result in results) == 2
    assert sum(result.match_id is not None for result in results) == 1
    assert await count_rows(store, Reaction) == 2
    assert await count_rows(store, Match) == 1
    bot = SimpleNamespace(send_message=AsyncMock())
    for (actor, _), result in zip(requests, results, strict=True):
        await notify_decision(bot, store, actor.telegram_id, result, "like")
    assert bot.send_message.await_count == 3


async def make_match(store, a, b):
    await store.decide(a.id, b.id, "like")
    return (await store.decide(b.id, a.id, "like")).match_id


async def test_contact_authorization_current_username_and_hidden_matches(store, make_user):
    a, b, stranger = await make_user(), await make_user(), await make_user()
    bot = SimpleNamespace(
        get_chat=AsyncMock(
            return_value=SimpleNamespace(id=b.telegram_id, type="private", username="new_username")
        )
    )
    with pytest.raises(RuleError):
        await contact_url(bot, store, a.id, 999)
    bot.get_chat.assert_not_called()
    match_id = await make_match(store, a, b)
    with pytest.raises(RuleError):
        await contact_url(bot, store, stranger.id, match_id)
    bot.get_chat.assert_not_called()
    await store.set_active(a.id, False)
    await store.set_active(b.id, False)
    assert await contact_url(bot, store, a.id, match_id) == "https://t.me/new_username"
    bot.get_chat.assert_awaited_once_with(b.telegram_id)
    assert len(await store.match_page(a.id, 0)) == 1
    bot.get_chat.return_value.username = None
    assert await contact_url(bot, store, a.id, match_id) is None
    assert not (await store.profile(b.id)).is_active
    bot.get_chat.side_effect = TelegramNetworkError(
        method=GetChat(chat_id=b.telegram_id), message="offline"
    )
    assert await contact_url(bot, store, a.id, match_id) is None


@pytest.mark.parametrize("change", ["ban", "block", "delete"])
async def test_contact_rechecks_after_network_await(store, make_user, change):
    a, b = await make_user(), await make_user()
    match_id = await make_match(store, a, b)

    async def racing_get_chat(_telegram_id):
        if change == "ban":
            await store.ban_by_telegram(900_001, b.telegram_id, True)
        elif change == "block":
            await store.block(b.id, a.id)
        else:
            await store.delete_profile(b.id)
        return SimpleNamespace(id=b.telegram_id, type="private", username="present")

    bot = SimpleNamespace(get_chat=AsyncMock(side_effect=racing_get_chat))
    with pytest.raises(RuleError):
        await contact_url(bot, store, a.id, match_id)


async def test_report_deduplicates_blocks_and_survives_deletion(store, make_user):
    a, b = await make_user(), await make_user()
    match_id = await make_match(store, a, b)
    await asyncio.gather(*(store.report(a.id, b.id, "Spam") for _ in range(4)))
    assert await count_rows(store, Report) == 1
    assert await count_rows(store, Block) == 1
    assert await store.match_page(a.id, 0) == []
    with pytest.raises(RuleError):
        await store.match_target(a.id, match_id)
    await store.ban_by_telegram(900_001, b.telegram_id, True)
    await store.delete_profile(b.id)
    assert await store.profile(b.id) is None
    assert await count_rows(store, Match) == 0
    assert await count_rows(store, Reaction) == 0
    assert await count_rows(store, Report) == 1
    assert await count_rows(store, Block) == 1
    async with store.db.sessions() as session:
        deleted_user = await session.get(User, b.id)
        assert deleted_user.is_banned
        assert deleted_user.username is None
    await store.sync_user(b.telegram_id, "returned")
    with pytest.raises(RuleError):
        await store.save_profile(
            b.id,
            dict(
                name="Ali",
                age=25,
                gender="male",
                seeking="any",
                city="Toshkent",
                bio="",
                photo_file_id="id",
                consent_at=utcnow(),
            ),
        )


async def test_admin_authorization_and_unban_stays_hidden(store, make_user):
    a, b = await make_user(), await make_user()
    await store.report(a.id, b.id, "Spam")
    report_id = (await store.report_page(900_001, 0))[0].id
    with pytest.raises(RuleError):
        await store.ban_by_telegram(a.telegram_id, b.telegram_id, True)
    with pytest.raises(RuleError):
        await store.admin_action(a.telegram_id, report_id, "ban")
    with pytest.raises(RuleError):
        await store.report_page(a.telegram_id, 0)
    await store.sync_user(900_001, "admin")
    await store.admin_action(900_001, report_id, "ban")
    with pytest.raises(RuleError):
        await store.decide(b.id, a.id, "like")
    await store.admin_action(900_001, report_id, "unban")
    assert not (await store.profile(b.id)).is_active
    await store.admin_action(900_001, report_id, "review")
    assert await store.report_page(900_001, 0) == []


@pytest.mark.parametrize(
    "error",
    [
        TelegramForbiddenError,
        TelegramBadRequest,
        TelegramNetworkError,
        TelegramRetryAfter,
        TelegramServerError,
    ],
)
async def test_failed_notification_preserves_match(store, make_user, error):
    a, b = await make_user(), await make_user()
    await store.decide(a.id, b.id, "like")
    decision = await store.decide(b.id, a.id, "like")
    kwargs = {"retry_after": 2} if error is TelegramRetryAfter else {}
    failure = error(
        method=SendMessage(chat_id=a.telegram_id, text="test"), message="test failure", **kwargs
    )
    calls = []

    async def send(recipient, *_args, **_kwargs):
        calls.append(recipient)
        if len(calls) == 1:
            raise failure

    bot = SimpleNamespace(send_message=AsyncMock(side_effect=send))
    await notify_decision(bot, store, b.telegram_id, decision, "like")
    assert len(calls) == 2
    assert await count_rows(store, Match) == 1
    assert len(await store.match_page(a.id, 0)) == 1
    if error is TelegramForbiddenError:
        assert not (await store.profile(b.id)).is_active


async def test_restart_persists_profile_reaction_match(store, make_user):
    a, b = await make_user(), await make_user()
    match_id = await make_match(store, a, b)
    url = store.db.engine.url.render_as_string(hide_password=False)
    await store.db.close()
    reopened = Store(Database(url), [900_001])
    try:
        assert (await reopened.profile(a.id)).name == "Ali"
        assert len(await reopened.match_page(a.id, 0)) == 1
        assert (await reopened.match_target(a.id, match_id)).id == b.id
        assert not (await reopened.decide(a.id, b.id, "like")).created
    finally:
        await reopened.db.close()
