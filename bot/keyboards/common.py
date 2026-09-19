from typing import Literal, TypeAlias

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.texts import MENU_LABELS

ButtonStyle: TypeAlias = Literal["primary", "success", "danger"]
ButtonSpec: TypeAlias = tuple[str, str] | tuple[str, str, ButtonStyle]


def inline(*rows: tuple[ButtonSpec, ...]) -> InlineKeyboardMarkup:
    keyboard = []
    for row in rows:
        buttons = []
        for item in row:
            label, data, *optional_style = item
            extra = {"style": optional_style[0]} if optional_style else {}
            buttons.append(InlineKeyboardButton(text=label, callback_data=data, **extra))
        keyboard.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def menu() -> InlineKeyboardMarkup:
    """Main navigation.

    Callback buttons keep navigation inside the bot message and do not echo their
    labels into the chat as user messages.
    """
    return inline(
        ((MENU_LABELS[0], "discover", "primary"),),
        ((MENU_LABELS[1], "profile"), (MENU_LABELS[2], "incoming")),
        ((MENU_LABELS[3], "matches:0"),),
        ((MENU_LABELS[4], "settings"), (MENU_LABELS[5], "help")),
    )


def location_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📍 Отправить геолокацию", request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder="Отправь геолокацию 📍",
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def home() -> InlineKeyboardMarkup:
    return inline((("⚙️ Настройки", "settings"), ("🏠 В меню", "home")))


def decisions(target: int, incoming: bool = False) -> InlineKeyboardMarkup:
    source = "i" if incoming else "d"
    return inline(
        (
            ("💜 Нравится", f"react:{target}:like:{source}"),
            ("Дальше ➡️", f"react:{target}:pass:{source}"),
        ),
        (("🚫 Заблокировать", f"block:{target}"), ("⚠️ Пожаловаться", f"report:{target}")),
        (("🏠 В меню", "home"),),
    )


def profile_menu(active: bool) -> InlineKeyboardMarkup:
    return inline(
        (("Имя", "edit:name"), ("Возраст", "edit:age")),
        (("Пол", "edit:gender"), ("Кого я ищу", "edit:seeking")),
        (("📍 Местоположение", "edit:location"),),
        (("Описание", "edit:bio"), ("Фото", "edit:photo_file_id")),
        (
            (
                ("Скрыть анкету" if active else "Показать анкету"),
                "active:0" if active else "active:1",
            ),
        ),
        (("🗑 Удалить анкету", "delete"),),
        (("🏠 В меню", "home"),),
    )


def genders(prefix: str, any_gender: bool = False) -> InlineKeyboardMarkup:
    choices: list[ButtonSpec] = [
        ("Мужчина", f"{prefix}:male"),
        ("Женщина", f"{prefix}:female"),
    ]
    if any_gender:
        choices.append(("Неважно", f"{prefix}:any"))
    return inline(tuple(choices))


def match_actions(match_id: int, target: int) -> InlineKeyboardMarkup:
    return inline(
        (("💬 Открыть контакт", f"contact:{match_id}", "primary"),),
        (("🚫 Заблокировать", f"block:{target}"), ("⚠️ Пожаловаться", f"report:{target}")),
        (("✨ Взаимные симпатии", "matches:0"), ("🏠 В меню", "home")),
    )
