from datetime import UTC, datetime
from itertools import count
from types import SimpleNamespace
from typing import Any, cast
from unittest.mock import AsyncMock

import pytest
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import AnswerCallbackQuery, GetChat, SendMessage, SendPhoto
from aiogram.types import (
    AcceptedGiftTypes,
    CallbackQuery,
    Chat,
    ChatFullInfo,
    InlineKeyboardMarkup,
    Location,
    Message,
    PhotoSize,
    Update,
    User,
)
from sqlalchemy import select

from bot.db.models import Match, Report
from bot.handlers.discovery import MESSAGE_ID_KEY, PHOTO_ID_KEY, _show_profile, show_next
from bot.keyboards.common import decisions
from bot.main import create_dispatcher
from bot.services.telegram import caption
from bot.texts import LEGACY_MENU_LABELS, MENU_LABELS, PREVIOUS_MENU_LABELS


async def test_full_dispatcher_flow_offline(store, make_user, monkeypatch):
    """Real aiogram routing/FSM/middleware with a mocked HTTP session."""
    dispatcher = create_dispatcher(store)
    bot = Bot("123456:OFFLINE_TEST_TOKEN", default=DefaultBotProperties(parse_mode="HTML"))
    calls = []
    sequence = count(1)

    async def request(_bot, method, **_kwargs):
        del _bot, _kwargs
        calls.append(method)
        if isinstance(method, (SendMessage, SendPhoto)):
            return Message(
                message_id=cast(int, next(sequence)),
                date=cast(datetime, datetime.now(UTC)),
                chat=cast(Chat, Chat(id=int(method.chat_id), type="private")),
                text=getattr(method, "text", None),
                reply_markup=(
                    cast(InlineKeyboardMarkup, method.reply_markup)
                    if hasattr(method.reply_markup, "inline_keyboard")
                    else None
                ),
            )
        if isinstance(method, GetChat):
            return ChatFullInfo(
                id=int(method.chat_id),
                type="private",
                first_name="Test",
                username="current_name",
                accent_color_id=1,
                max_reaction_count=11,
                accepted_gift_types=AcceptedGiftTypes(
                    unlimited_gifts=False,
                    limited_gifts=False,
                    unique_gifts=False,
                    premium_subscription=False,
                ),
            )
        return True

    monkeypatch.setattr(bot.session, "make_request", request)
    tid = 700_001
    has_username = False

    async def feed(*, text=None, callback=None, photo=False, location=None, actor=tid, group=False):
        sender = User(
            id=actor,
            is_bot=False,
            first_name="User",
            username=f"user_{actor}" if has_username else None,
        )
        chat = Chat(id=-10001 if group else actor, type="group" if group else "private")
        payload = dict(
            message_id=next(sequence),
            date=datetime.now(UTC),
            chat=chat,
            from_user=sender,
            text=text,
        )
        if photo:
            payload["photo"] = [
                PhotoSize(file_id="photo-id", file_unique_id="unique", width=640, height=640)
            ]
        if location:
            payload["location"] = Location(latitude=location[0], longitude=location[1])
        if callback:
            update = Update(
                update_id=next(sequence),
                callback_query=CallbackQuery(
                    id=str(next(sequence)),
                    from_user=sender,
                    chat_instance="test",
                    message=Message(**cast(dict[str, Any], payload)),
                    data=callback,
                ),
            )
        else:
            update = Update(
                update_id=next(sequence),
                message=Message(**cast(dict[str, Any], payload)),
            )
        await dispatcher.feed_update(bot, update)

    def last_text():
        return next(method.text for method in reversed(calls) if isinstance(method, SendMessage))

    try:
        await feed(text="/start", group=True)
        assert not calls
        await feed(text="/start")
        await feed(callback="reg:adult")
        await feed(callback="reg:consent")
        assert "Telegram username" in last_text()
        await feed(callback="reg:username")
        assert "Telegram username" in last_text()
        has_username = True
        await feed(callback="reg:username")
        assert "Как тебя зовут" in last_text()
        await feed(text="@contact")
        assert "Не указывай контакты" in last_text()
        await feed(text="Malika")
        await feed(text="17")
        assert "Возраст должен быть от 18 до 99 лет" in last_text()
        await feed(text="25")
        await feed(callback="reg:gender:female")
        await feed(callback="reg:seeking:any")
        await feed(location=(42.8746, 74.5698))
        await feed(callback="reg:skip")
        await feed(text="not a photo")
        assert "фотографию" in last_text()
        user = await store.sync_user(tid, f"user_{tid}")
        assert await store.profile(user.id) is None
        await feed(photo=True)
        assert isinstance(calls[-1], SendPhoto)
        assert await store.profile(user.id) is None
        await feed(callback="reg:save")
        saved = await store.profile(user.id)
        assert saved.name == "Malika" and saved.latitude == 42.8746 and saved.longitude == 74.5698
        await feed(text="/start")
        assert "Хорошо, что ты здесь" in last_text()

        # Edits don't touch the saved row until valid input is submitted.
        await feed(callback="edit:name")
        await feed(text="/cancel")
        assert (await store.profile(user.id)).name == "Malika"
        await feed(callback="edit:location")
        state = dispatcher.fsm.get_context(bot=bot, chat_id=tid, user_id=tid)
        await state.clear()  # The same loss of unfinished state as a restart.
        await feed(text="/start")
        assert (await store.profile(user.id)).latitude == 42.8746
        await feed(callback="edit:bio")
        await feed(callback="editvalue:empty")
        await feed(callback="edit:age")
        await feed(text="26")
        assert (await store.profile(user.id)).age == 26
        await feed(callback="settings:age")
        await feed(text="40 20")
        assert "не должен быть больше" in last_text()
        await feed(text="20 35")
        await feed(callback="edit:location")
        await feed(location=(42.88, 74.57))
        assert (await store.profile(user.id)).latitude == 42.88

        other = await make_user(latitude=42.87, longitude=74.58)
        # The previous Russian help button remains routable too.
        await feed(text=PREVIOUS_MENU_LABELS[5])
        assert "❔ Помощь" in last_text()
        # Existing Uzbek reply keyboards remain usable after the UI translation.
        await feed(text=LEGACY_MENU_LABELS[0])
        assert isinstance(calls[-1], SendPhoto)
        assert "user_" not in calls[-1].caption
        await feed(callback=f"react:{other.id}:like:d")
        assert any(
            isinstance(call, SendMessage) and "понравилась твоя анкета" in call.text
            for call in calls
        )
        await feed(callback=f"react:{other.id}:like:d")
        assert "Подожди секунду" in last_text()
        await feed(callback=f"react:{user.id}:like:d", actor=other.telegram_id)
        async with store.db.sessions() as session:
            match_id = await session.scalar(select(Match.id))
        assert match_id
        await feed(text=MENU_LABELS[3])
        await feed(callback=f"match:{match_id}")
        await feed(callback=f"contact:{match_id}")
        assert "https://t.me/current_name" in last_text()
        stranger = await make_user()
        before = len([call for call in calls if isinstance(call, GetChat)])
        await feed(callback=f"contact:{match_id}", actor=stranger.telegram_id)
        assert "недоступна" in last_text()
        assert len([call for call in calls if isinstance(call, GetChat)]) == before
        await feed(text=f"/ban {other.telegram_id}")
        assert "администратору" in last_text()
        await feed(callback="admin:ban:1")
        assert "администратору" in last_text()

        await feed(callback=f"report:{other.id}")
        await feed(callback="reason:other")
        await feed(text="Sinov shikoyati")
        await feed(callback="reportconfirm")
        assert "Жалоба сохранена" in last_text()
        assert await store.match_page(user.id, 0) == []
        async with store.db.sessions() as session:
            report_id = await session.scalar(select(Report.id))
        await feed(text="/admin", actor=900_001)
        await feed(callback="admin:list:0", actor=900_001)
        await feed(callback=f"admin:open:{report_id}", actor=900_001)
        await feed(callback=f"admin:ban:{report_id}", actor=900_001)
        # Bans apply to old callback buttons as well as ordinary messages.
        await feed(callback=f"react:{stranger.id}:like:d", actor=other.telegram_id)
        assert "ограничен" in last_text()
        await feed(text="/privacy", actor=other.telegram_id)
        assert "администратор" in last_text()
        await feed(text="/id", actor=other.telegram_id)
        assert str(other.telegram_id) in last_text()
        await feed(text="/delete", actor=other.telegram_id)
        await feed(callback="delete:yes", actor=other.telegram_id)
        assert await store.profile(other.id) is None
        await feed(callback="reg:save")
        assert "устарела" in last_text()
        await feed(callback="react:bad-id:like:d", actor=stranger.telegram_id)
        assert "недействительна" in last_text()
        answers = [call for call in calls if isinstance(call, AnswerCallbackQuery)]
        assert len(answers) >= 25
    finally:
        await dispatcher.fsm.close()
        await bot.session.close()


async def test_failing_photo_hides_user_and_keeps_saved_profile(store, make_user):
    from aiogram.exceptions import TelegramForbiddenError

    from bot.middlewares.access import AccessMiddleware

    user = await make_user()
    message = Message(
        message_id=1,
        date=datetime.now(UTC),
        chat=Chat(id=user.telegram_id, type="private"),
        from_user=User(
            id=user.telegram_id, is_bot=False, first_name="Test", username=user.username
        ),
        text="test",
    )
    handler = AsyncMock(
        side_effect=TelegramForbiddenError(
            method=SendMessage(chat_id=user.telegram_id, text="test"), message="blocked"
        )
    )
    bot = SimpleNamespace(send_message=AsyncMock())
    await AccessMiddleware(store)(handler, message, {"bot": bot})
    assert not (await store.profile(user.id)).is_active
    bot.send_message.assert_not_called()


async def test_ten_discovery_profiles_reuse_one_message(store, make_user):
    actor = await make_user(name="Viewer")
    candidates = []
    for index in range(10):
        photo = "shared-photo" if index < 2 else f"photo-{index}"
        candidate = await make_user(name=f"Person {index}", photo_file_id=photo)
        candidates.append(candidate)

    profile_message_id = 9_001
    state_data = {}
    state = SimpleNamespace(
        get_data=AsyncMock(side_effect=lambda: state_data.copy()),
        update_data=AsyncMock(side_effect=lambda **values: state_data.update(values)),
    )
    bot = SimpleNamespace(
        edit_message_caption=AsyncMock(),
        edit_message_media=AsyncMock(),
    )
    message = SimpleNamespace(
        bot=bot,
        chat=SimpleNamespace(id=actor.telegram_id),
        answer=AsyncMock(),
        answer_photo=AsyncMock(return_value=SimpleNamespace(message_id=profile_message_id)),
    )

    await show_next(message, state, store, actor)
    for candidate in candidates[:9]:
        result = await store.decide(actor.id, candidate.id, "pass")
        assert result.created
        await show_next(message, state, store, actor)

    message.answer_photo.assert_awaited_once()
    assert bot.edit_message_caption.await_count == 1
    assert bot.edit_message_media.await_count == 8
    assert state_data[MESSAGE_ID_KEY] == profile_message_id
    assert state_data[PHOTO_ID_KEY] == "photo-9"

    first_edit = bot.edit_message_caption.await_args
    second_profile = await store.profile(candidates[1].id)
    assert first_edit.kwargs == {
        "chat_id": actor.telegram_id,
        "message_id": profile_message_id,
        "caption": caption(second_profile),
        "reply_markup": decisions(candidates[1].id),
    }

    for edit, expected_user in zip(
        bot.edit_message_media.await_args_list, candidates[2:], strict=True
    ):
        profile = await store.profile(expected_user.id)
        assert edit.kwargs["chat_id"] == actor.telegram_id
        assert edit.kwargs["message_id"] == profile_message_id
        assert edit.kwargs["media"].media == profile.photo_file_id
        assert edit.kwargs["media"].caption == caption(profile)
        assert edit.kwargs["reply_markup"] == decisions(expected_user.id)


async def test_discovery_edit_failure_handling(store, make_user):
    from aiogram.methods import EditMessageMedia

    candidate = await make_user(name="Candidate", photo_file_id="new-photo")
    profile = await store.profile(candidate.id)
    method = EditMessageMedia(
        chat_id=candidate.telegram_id,
        message_id=77,
        media={"type": "photo", "media": "new-photo"},
    )
    state = AsyncMock()
    state.get_data.return_value = {MESSAGE_ID_KEY: 77, PHOTO_ID_KEY: "old-photo"}
    bot = SimpleNamespace(edit_message_media=AsyncMock())
    message = SimpleNamespace(
        bot=bot,
        chat=SimpleNamespace(id=candidate.telegram_id),
        answer_photo=AsyncMock(return_value=SimpleNamespace(message_id=88)),
    )

    bot.edit_message_media.side_effect = TelegramBadRequest(
        method=method, message="Bad Request: message is not modified"
    )
    await _show_profile(message, state, profile, False)
    message.answer_photo.assert_not_awaited()

    bot.edit_message_media.side_effect = TelegramBadRequest(
        method=method, message="Bad Request: message to edit not found"
    )
    await _show_profile(message, state, profile, False)
    message.answer_photo.assert_awaited_once()
    assert state.update_data.await_args.kwargs == {
        MESSAGE_ID_KEY: 88,
        PHOTO_ID_KEY: "new-photo",
    }

    message.answer_photo.reset_mock()
    bot.edit_message_media.side_effect = TelegramBadRequest(
        method=method, message="Bad Request: wrong file identifier"
    )
    with pytest.raises(TelegramBadRequest, match="wrong file identifier"):
        await _show_profile(message, state, profile, False)
    message.answer_photo.assert_not_awaited()
