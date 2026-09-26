from typing import Any, Literal, TypeAlias, cast

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)

from bot.i18n import tr

ButtonStyle: TypeAlias = Literal["primary", "success", "danger"]
ButtonSpec: TypeAlias = tuple[str, str] | tuple[str, str, ButtonStyle]


def inline(*rows: tuple[ButtonSpec, ...]) -> InlineKeyboardMarkup:
    keyboard = []
    for row in rows:
        buttons = []
        for item in row:
            label, data, *optional_style = item
            extra = {"style": optional_style[0]} if optional_style else {}
            buttons.append(
                InlineKeyboardButton(
                    text=label,
                    callback_data=data,
                    **cast(Any, extra),
                )
            )
        keyboard.append(buttons)
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def menu() -> ReplyKeyboardMarkup:
    labels = [
        tr(f"menu_{key}")
        for key in ("discover", "profile", "likes", "matches", "settings", "premium", "help")
    ]
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=labels[0], style="primary")],
            [KeyboardButton(text=labels[1]), KeyboardButton(text=labels[2])],
            [KeyboardButton(text=labels[3])],
            [KeyboardButton(text=labels[4]), KeyboardButton(text=labels[5])],
            [KeyboardButton(text=labels[6])],
        ],
        resize_keyboard=True,
        input_field_placeholder=tr("menu_placeholder"),
    )


def location_request() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=tr("send_location"), request_location=True)]],
        resize_keyboard=True,
        one_time_keyboard=True,
        input_field_placeholder=tr("send_location_placeholder"),
    )


def remove_keyboard() -> ReplyKeyboardRemove:
    return ReplyKeyboardRemove()


def language_selection() -> InlineKeyboardMarkup:
    return inline(
        (("🇺🇿 O'zbekcha", "lang:uz"), ("🇷🇺 Русский", "lang:ru")),
        (("🇬🇧 English", "lang:en"), ("🇰🇬 Кыргызча", "lang:kg")),
    )


def language_continue(label: str) -> InlineKeyboardMarkup:
    return inline(((label, "home"),))


def home() -> InlineKeyboardMarkup:
    return inline(((tr("menu_settings"), "settings"), (tr("back_menu"), "home")))


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
            (tr("like"), f"react:{target}:like:{source}"),
            (tr("pass"), f"react:{target}:pass:{source}"),
        ),
    )
    if can_undo:
        rows.append(((tr("return_profile"), "undo:pass"),))
    rows.extend(
        [
            ((tr("block_profile"), f"block:{target}"), (tr("report_profile"), f"report:{target}")),
            ((tr("back_menu"), "home"),),
        ]
    )
    return inline(*rows)


def profile_menu(active: bool) -> InlineKeyboardMarkup:
    return inline(
        ((tr("name"), "edit:name"), (tr("age"), "edit:age")),
        ((tr("gender"), "edit:gender"), (tr("seeking"), "edit:seeking")),
        ((f"📍 {tr('location')}", "edit:location"),),
        ((tr("bio"), "edit:bio"), (tr("photo"), "edit:photo_file_id")),
        (
            (
                tr("hide_profile") if active else tr("show_profile"),
                "active:0" if active else "active:1",
            ),
        ),
        ((f"🗑 {tr('delete_profile')}", "delete"),),
        ((tr("back_menu"), "home"),),
    )


def genders(prefix: str, any_gender: bool = False) -> InlineKeyboardMarkup:
    choices: list[ButtonSpec] = [
        (tr("male"), f"{prefix}:male"),
        (tr("female"), f"{prefix}:female"),
    ]
    if any_gender:
        choices.append((tr("any"), f"{prefix}:any"))
    return inline(tuple(choices))


def match_actions(match_id: int, target: int) -> InlineKeyboardMarkup:
    return inline(
        ((tr("open_contact_short"), f"contact:{match_id}", "primary"),),
        ((tr("block_profile"), f"block:{target}"), (tr("report_profile"), f"report:{target}")),
        ((tr("matches_short"), "matches:0"), (tr("back_menu"), "home")),
    )
