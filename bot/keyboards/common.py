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


def menu() -> ReplyKeyboardMarkup:
    # aiogram 3.22 forwards Bot API fields it does not yet expose in its signature.
    # Telegram clients that do not render styles still see the complete action label.
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=MENU_LABELS[0], style="primary")],
            [KeyboardButton(text=MENU_LABELS[1]), KeyboardButton(text=MENU_LABELS[2])],
            [KeyboardButton(text=MENU_LABELS[3])],
            [KeyboardButton(text=MENU_LABELS[4]), KeyboardButton(text=MENU_LABELS[5])],
            [KeyboardButton(text=MENU_LABELS[6])],  # Помощь
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие 💜",
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


def decisions(
    target: int,
    incoming: bool = False,
    can_undo: bool = True,
    photo_index: int = 0,
    photo_count: int = 1,
) -> InlineKeyboardMarkup:
    source = "i" if incoming else "d"
    rows: list[tuple[ButtonSpec, ...]] = []

    # Photo gallery navigation if multiple photos
    if photo_count > 1:
        prev_idx = (photo_index - 1) % photo_count
        next_idx = (photo_index + 1) % photo_count
        rows.append(
            (
                ("◀️", f"photo:{target}:{prev_idx}:{source}"),
                (f"{photo_index + 1}/{photo_count}", f"photo:info:{photo_index + 1}/{photo_count}"),
                ("▶️", f"photo:{target}:{next_idx}:{source}"),
            )
        )

    rows.append(
        (
            ("💜 Нравится", f"react:{target}:like:{source}"),
            ("Дальше ➡️", f"react:{target}:pass:{source}"),
        ),
    )
    if can_undo:
        rows.append((("⏪ Вернуть анкету", "undo:pass"),))
    rows.extend([
        (("🚫 Заблокировать", f"block:{target}"), ("⚠️ Пожаловаться", f"report:{target}")),
        (("🏠 В меню", "home"),),
    ])
    return inline(*rows)


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
