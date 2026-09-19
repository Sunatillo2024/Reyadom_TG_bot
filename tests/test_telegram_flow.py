from datetime import UTC, datetime
from itertools import count
from types import SimpleNamespace
from unittest.mock import AsyncMock

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.methods import (
    AnswerCallbackQuery,
    EditMessageCaption,
    EditMessageMedia,
    EditMessageReplyMarkup,
    EditMessageText,
    GetChat,
    SendMessage,
    SendPhoto,
)
from aiogram.types import Chat, ChatFullInfo, Location, Message, PhotoSize, Update, User
from sqlalchemy import select

from bot.db.models import Match, Report
from bot.main import create_dispatcher
from bot.texts import LEGACY_MENU_LABELS, MENU_LABELS, PREVIOUS_MENU_LABELS


async def test_full_dispatcher_flow_offline(store, make_user, monkeypatch):
    """Real aiogram routing/FSM/middleware with a mocked HTTP session."""
    dispatcher = create_dispatcher(store)
    bot = Bot("123456:OFFLINE_TEST_TOKEN", default=DefaultBotProperties(parse_mode="HTML"))
    calls = []
    sequence = count(1)
    messages: dict[tuple[int, int], Message] = {}
    latest: dict[int, Message] = {}

    def bot_message(
        chat_id,
        message_id,
        *,
        text=None,
        caption=None,
        photo_id=None,
        reply_markup=None,
    ):
        result = Message(
            message_id=message_id,
            date=datetime.now(UTC),
            chat=Chat(id=int(chat_id), type="private"),
            from_user=User(id=123456, is_bot=True, first_name="Bot"),
            text=text,
            caption=caption,
            photo=(
                [
                    PhotoSize(
                        file_id=str(photo_id),
                        file_unique_id="bot-photo",
                        width=640,
                        height=640,
                    )
                ]
                if photo_id
                else None
            ),
            reply_markup=reply_markup,
        )
        result.as_(bot)
        messages[(int(chat_id), message_id)] = result
        latest[int(chat_id)] = result
        return result

    async def request(_bot, method, **_kwargs):
        calls.append(method)
        if isinstance(method, SendMessage):
            return bot_message(
                method.chat_id,
                next(sequence),
                text=method.text,
                reply_markup=(
                    method.reply_markup
                    if hasattr(method.reply_markup, "inline_keyboard")
                    else None
                ),
            )
        if isinstance(method, SendPhoto):
            return bot_message(
                method.chat_id,
                next(sequence),
                caption=method.caption,
                photo_id=method.photo,
                reply_markup=(
                    method.reply_markup
                    if hasattr(method.reply_markup, "inline_keyboard")
                    else None
                ),
            )
        if isinstance(
            method, (EditMessageText, EditMessageCaption, EditMessageMedia, EditMessageReplyMarkup)
        ):
            current = messages[(int(method.chat_id), method.message_id)]
            if isinstance(method, EditMessageText):
                return bot_message(
                    method.chat_id,
                    method.message_id,
                    text=method.text,
                    reply_markup=method.reply_markup,
                )
            if isinstance(method, EditMessageMedia):
                return bot_message(
                    method.chat_id,
                    method.message_id,
                    caption=method.media.caption,
                    photo_id=method.media.media,
                    reply_markup=method.reply_markup,
                )
            return bot_message(
                method.chat_id,
                method.message_id,
                text=current.text,
                caption=(
                    method.caption if isinstance(method, EditMessageCaption) else current.caption
                ),
                photo_id=current.photo[-1].file_id if current.photo else None,
                reply_markup=method.reply_markup,
            )
        if isinstance(method, GetChat):
            return ChatFullInfo(
                id=int(method.chat_id),
                type="private",
                first_name="Test",
                username="current_name",
                accent_color_id=1,
                max_reaction_count=11,
                accepted_gift_types={
                    "unlimited_gifts": False,
                    "limited_gifts": False,
                    "unique_gifts": False,
                    "premium_subscription": False,
                },
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
            source = latest.get(actor)
            if source:
                payload.update(
                    message_id=source.message_id,
                    text=source.text,
                    caption=source.caption,
                    photo=source.photo,
                    reply_markup=source.reply_markup,
                )
            update = Update(
                update_id=next(sequence),
                callback_query={
                    "id": str(next(sequence)),
                    "from_user": sender,
                    "chat_instance": "test",
                    "message": Message(**payload),
                    "data": callback,
                },
            )
        else:
            update = Update(update_id=next(sequence), message=Message(**payload))
        await dispatcher.feed_update(bot, update)

    def method_text(method):
        if isinstance(method, (SendMessage, EditMessageText)):
            return method.text
        if isinstance(method, (SendPhoto, EditMessageCaption)):
            return method.caption
        if isinstance(method, EditMessageMedia):
            return method.media.caption
        return None

    def last_text():
        return next(text for method in reversed(calls) if (text := method_text(method)) is not None)

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

        # Menu -> section -> back edits one bot message instead of sending more.
        home_message_id = latest[tid].message_id
        sent_before_navigation = len(
            [call for call in calls if isinstance(call, (SendMessage, SendPhoto))]
        )
        await feed(callback="profile")
        assert latest[tid].message_id == home_message_id
        await feed(callback="home")
        assert latest[tid].message_id == home_message_id
        assert len([call for call in calls if isinstance(call, (SendMessage, SendPhoto))]) == (
            sent_before_navigation
        )

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
        last_photo = next(call for call in reversed(calls) if isinstance(call, SendPhoto))
        assert "user_" not in last_photo.caption
        await feed(callback=f"react:{other.id}:like:d")
        assert any(
            isinstance(call, SendMessage) and "понравилась твоя анкета" in call.text
            for call in calls
        )
        duplicate_content_calls = len(
            [call for call in calls if method_text(call) is not None]
        )
        await feed(callback=f"react:{other.id}:like:d")
        assert len([call for call in calls if method_text(call) is not None]) == (
            duplicate_content_calls
        )
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
