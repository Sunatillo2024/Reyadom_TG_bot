from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from aiogram.types import CallbackQuery, Chat, Message, PhotoSize, ReplyKeyboardMarkup
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


async def test_profile_save_accepts_json_serialized_consent_timestamp(store):
    user = await store.sync_user(810_010, "redis_draft")
    draft = profile_draft(consent_at=datetime.now(UTC).isoformat())

    assert await store.save_profile(user.id, draft)
    assert (await store.profile(user.id)).consent_at.tzinfo is not None


async def test_profile_save_inherits_recorded_consent_when_draft_lacks_it(store):
    """Resumed anketa drafts skip the consent screens, so the user-row flag must
    satisfy the final save instead of rejecting a complete anketa."""
    user = await store.sync_user(810_011, "resumed_consent")
    await store.record_consent(user.id)
    draft = profile_draft()
    draft.pop("consent_at")

    assert await store.save_profile(user.id, draft)
    saved = await store.profile(user.id)
    assert saved is not None and saved.photo_file_id == "telegram-photo-id"
    assert saved.consent_at.tzinfo is not None


async def test_confirm_recovers_photo_from_preview_when_fsm_lost_it():
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from aiogram.fsm.storage.memory import MemoryStorage

    from bot.handlers.registration import save
    from bot.states import Registration

    storage = MemoryStorage()
    user_id = 810_014
    state = FSMContext(
        storage=storage,
        key=StorageKey(bot_id=1, chat_id=user_id, user_id=user_id),
    )
    await state.set_state(Registration.preview)
    await state.set_data(
        {
            "name": "Malika",
            "age": 25,
            "gender": "female",
            "seeking": "any",
            "city": "Bishkek",
            "bio": "Salom",
            "consent_at": datetime.now(UTC).isoformat(),
            "photo_file_id": None,
        }
    )
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=user_id, type="private"),
        from_user=TelegramUser(id=user_id, is_bot=False, first_name="Test"),
        photo=[PhotoSize(file_id="preview-photo", file_unique_id="unique", width=640, height=640)],
    )
    callback = CallbackQuery(
        id="confirm",
        from_user=message.from_user,
        chat_instance="test",
        message=message,
        data="reg:save",
    )
    store = SimpleNamespace(save_profile=AsyncMock())
    with patch.object(Message, "answer", new_callable=AsyncMock) as answer:
        await save(callback, state, store, SimpleNamespace(id=user_id))

    assert store.save_profile.await_args.args[0] == user_id
    assert store.save_profile.await_args.args[1]["photo_file_id"] == "preview-photo"
    assert await state.get_data() == {}
    assert isinstance(answer.await_args.kwargs["reply_markup"], ReplyKeyboardMarkup)


async def test_continue_registration_seeds_recorded_consent(store):
    from aiogram.fsm.context import FSMContext
    from aiogram.fsm.storage.base import StorageKey
    from aiogram.fsm.storage.memory import MemoryStorage

    from bot.handlers.registration import continue_registration
    from bot.states import Registration

    username = "resumed_state"
    user = await store.sync_user(810_013, username)
    await store.record_consent(user.id)
    user = await store.sync_user(user.telegram_id, username)
    assert user.consent_at is not None

    state = FSMContext(
        storage=MemoryStorage(),
        key=StorageKey(bot_id=1, chat_id=user.telegram_id, user_id=user.telegram_id),
    )
    message = SimpleNamespace(answer=AsyncMock())
    await continue_registration(message, state, user)

    assert (await state.get_data())["consent_at"] == user.consent_at.isoformat()
    assert await state.get_state() == Registration.name.state


async def test_profile_save_still_requires_photo_without_consent(store):
    user = await store.sync_user(810_012, "no_consent")
    draft = profile_draft()
    draft.pop("consent_at")

    with pytest.raises(RuleError):
        await store.save_profile(user.id, draft)
    assert await store.profile(user.id) is None


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
