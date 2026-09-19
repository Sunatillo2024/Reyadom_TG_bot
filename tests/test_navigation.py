from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import EditMessageText

from bot.keyboards.common import menu
from bot.services.telegram import update_navigation


def bad_request(message: str) -> TelegramBadRequest:
    return TelegramBadRequest(method=EditMessageText(text="test"), message=message)


async def test_navigation_ignores_message_not_modified():
    message = SimpleNamespace(
        photo=None,
        edit_text=AsyncMock(side_effect=bad_request("Bad Request: message is not modified")),
    )

    result = await update_navigation(message, "Same", menu())

    assert result is message


async def test_navigation_replaces_uneditable_message():
    replacement = SimpleNamespace(edit_reply_markup=AsyncMock())
    replacement.edit_reply_markup.return_value = replacement
    message = SimpleNamespace(
        photo=None,
        edit_reply_markup=AsyncMock(
            side_effect=bad_request("Bad Request: message to edit not found")
        ),
        answer_photo=AsyncMock(return_value=replacement),
    )

    result = await update_navigation(message, "Profile", menu(), photo="photo-file-id")

    assert result is replacement
    message.answer_photo.assert_awaited_once()
    replacement.edit_reply_markup.assert_awaited_once_with(reply_markup=menu())


async def test_navigation_does_not_hide_unexpected_bad_request():
    message = SimpleNamespace(
        photo=None,
        edit_text=AsyncMock(side_effect=bad_request("Bad Request: can't parse entities")),
    )

    with pytest.raises(TelegramBadRequest, match="can't parse entities"):
        await update_navigation(message, "<broken", menu())
