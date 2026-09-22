from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.types import Chat, Message
from aiogram.types import User as TelegramUser
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from bot.db.models import Profile, ProfilePhoto
from bot.middlewares.access import AccessMiddleware
from bot.services.validation import RuleError
from bot.texts import TEMPORARY_ERROR


def profile_draft(**changes):
    draft = {
        "name": "Malika",
        "age": 25,
        "gender": "female",
        "seeking": "any",
        "city": "Bishkek",
        "bio": "Salom",
        "photo_file_id": "telegram-photo-id",
        "consent_at": datetime.now(UTC),
    }
    draft.update(changes)
    return draft


async def row_count(store, model) -> int:
    async with store.db.sessions() as session:
        return await session.scalar(select(func.count()).select_from(model)) or 0


async def test_profile_save_is_idempotent(store):
    user = await store.sync_user(810_001, "new_profile")

    assert await store.save_profile(user.id, profile_draft())
    assert not await store.save_profile(user.id, {})

    assert await row_count(store, Profile) == 1
    assert await row_count(store, ProfilePhoto) == 1


async def test_profile_save_replaces_legacy_orphan_photo(store):
    user = await store.sync_user(810_002, "orphan_photo")
    async with store.db.sessions.begin() as session:
        session.add(
            ProfilePhoto(
                user_id=user.id,
                file_id="old-photo",
                is_primary=True,
                position=0,
                created_at=datetime.now(UTC),
            )
        )

    assert await store.save_profile(user.id, profile_draft(photo_file_id="new-photo"))

    async with store.db.sessions() as session:
        photos = list(
            await session.scalars(select(ProfilePhoto).where(ProfilePhoto.user_id == user.id))
        )
    assert [(photo.file_id, photo.position) for photo in photos] == [("new-photo", 0)]


@pytest.mark.parametrize(
    "changes",
    [
        {"latitude": "not-a-number", "longitude": 74.6},
        {"latitude": 42.9},
        {"bio": "x" * 301},
    ],
)
async def test_invalid_registration_data_is_a_rule_error(store, changes):
    user = await store.sync_user(810_003, "invalid_profile")

    with pytest.raises(RuleError):
        await store.save_profile(user.id, profile_draft(**changes))

    assert await store.profile(user.id) is None


async def test_database_error_rolls_back_the_whole_profile(store):
    user = await store.sync_user(810_004, "rollback_profile")

    with pytest.raises(SQLAlchemyError):
        await store.save_profile(user.id, profile_draft(photo_file_id="x" * 513))

    assert await store.profile(user.id) is None
    assert await row_count(store, ProfilePhoto) == 0
    assert await store.save_profile(user.id, profile_draft(photo_file_id="valid-photo"))


async def test_generic_message_is_only_used_for_unexpected_errors(store):
    telegram_id = 810_005
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=telegram_id, type="private"),
        from_user=TelegramUser(
            id=telegram_id,
            is_bot=False,
            first_name="Test",
            username="middleware_user",
        ),
        text="test",
    )
    bot = SimpleNamespace(send_message=AsyncMock())
    middleware = AccessMiddleware(store)

    await middleware(
        AsyncMock(side_effect=RuleError("Проверь данные анкеты.")), message, {"bot": bot}
    )
    assert bot.send_message.await_args.args[1] == "Проверь данные анкеты."

    bot.send_message.reset_mock()
    await middleware(AsyncMock(side_effect=RuntimeError("server failure")), message, {"bot": bot})
    assert bot.send_message.await_args.args[1] == TEMPORARY_ERROR
