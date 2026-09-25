from __future__ import annotations

from contextvars import ContextVar
from typing import Final

LANGUAGES: Final = ("ru", "uz", "en")
DEFAULT_LANGUAGE: Final = "ru"
current_language: ContextVar[str | None] = ContextVar("current_language", default=None)
LANGUAGE_NAMES: Final = {"uz": "🇺🇿 O'zbekcha", "ru": "🇷🇺 Русский", "en": "🇬🇧 English"}

_COMMON: Final = {
    "menu_discover": "💜 Смотреть анкеты",
    "menu_profile": "👤 Моя анкета",
    "menu_likes": "💌 Лайки",
    "menu_matches": "✨ Взаимные симпатии",
    "menu_settings": "⚙️ Настройки",
    "menu_premium": "💎 Premium",
    "menu_help": "❔ Помощь",
    "menu_placeholder": "Выбери действие 💜",
    "home": "<b>💜 Хорошо, что ты здесь!</b>\nПосмотри анкеты или загляни в свои симпатии.",
    "profile_missing": "Анкета не найдена. Создай её с помощью /start.",
    "profile_photo_error": ("Не удалось открыть прежнюю фотографию. Нажми «Фото» и загрузи новую."),
    "profile_status_active": "<b>Статус анкеты:</b> активна",
    "profile_status_hidden": "<b>Статус анкеты:</b> скрыта",
    "location_set": "указана",
    "location_unset": "не указана",
    "search_settings": (
        "<b>⚙️ Настройки поиска</b>\nВозраст: {min_age}–{max_age}\nГеолокация: {location}"
    ),
    "age_search": "Возраст для поиска",
    "change_location": "📍 Изменить геолокацию",
    "seeking_label": "Кого я ищу",
    "back_menu": "🏠 В меню",
    "profile_saved": "<b>Готово!</b> Анкета обновлена 💜",
    "next": "Дальше ➡️",
    "like": "💜 Нравится",
    "undo": "⏪ Вернуть анкету",
    "block": "🚫 Заблокировать",
    "report": "⚠️ Пожаловаться",
    "open_contact": "💬 Открыть контакт",
    "view_likes": "💌 Посмотреть лайки",
    "view_profile": "💜 Посмотреть анкету",
    "send_location": "📍 Отправить геолокацию",
    "send_location_placeholder": "Отправь геолокацию 📍",
    "edit_name": "<b>Новое имя</b>\nОтправь от 2 до 40 символов.",
    "edit_age": "<b>Новый возраст</b>\nОтправь целое число от 18 до 99.",
    "edit_city": "<b>Новый город</b>\nОтправь от 2 до 60 символов.",
    "edit_bio": "<b>Новое описание</b>\nОтправь до 300 символов.",
    "edit_gender": "<b>Выбери пол</b>",
    "edit_seeking": "<b>Кого ты ищешь?</b>",
    "edit_location": "<b>Новое местоположение 📍</b>\nОтправь геолокацию кнопкой ниже.",
    "edit_photo": "<b>Новое фото</b>\nОтправь одну фотографию как фото.",
    "age_search_prompt": "<b>Возраст для поиска</b>\nОтправь минимальный и максимальный возраст через пробел, например: 20 35.",  # noqa: E501
    "profile_visible": "<b>Анкета снова видна 💜</b>\nТеперь её могут увидеть другие пользователи.",
    "profile_hidden": "<b>Анкета скрыта</b>\nНовые пользователи не увидят её в поиске.",
    "search_saved": "<b>Готово!</b> Настройки поиска сохранены 💜",
    "access_restricted": "<b>Доступ ограничен</b>\nТы можешь использовать /help, /privacy, /id и /delete.",  # noqa: E501
    "pass": "Дальше ➡️",
    "return_profile": "Вернуть анкету",
    "block_profile": "Заблокировать",
    "report_profile": "Пожаловаться",
    "open_contact_short": "Открыть контакт",
    "matches_short": "Взаимные симпатии",
    "matches_title_page": "<b>✨ Взаимные симпатии</b>\nСтраница {page}",
    "no_matches": "<b>Взаимных симпатий пока нет 💜</b>\nПосмотри анкеты — знакомство может начаться с одного лайка.",  # noqa: E501
    "name": "Имя",
    "age": "Возраст",
    "gender": "Пол",
    "seeking": "Кого я ищу",
    "location": "Местоположение",
    "bio": "Описание",
    "photo": "Фото",
    "hide_profile": "Скрыть анкету",
    "show_profile": "Показать анкету",
    "delete_profile": "Удалить анкету",
    "male": "Мужчина",
    "female": "Женщина",
    "any": "Неважно",
}
_UZ: Final = {
    "menu_discover": "💜 Profil ko'rish",
    "menu_profile": "👤 Mening profilim",
    "menu_likes": "💌 Like'lar",
    "menu_matches": "✨ O'zaro simpatiyalar",
    "menu_settings": "⚙️ Sozlamalar",
    "menu_premium": "💎 Premium",
    "menu_help": "❔ Yordam",
    "menu_placeholder": "Amalni tanlang 💜",
    "home": (
        "<b>💜 Yaxshi, bu yerdasan!</b>\n"
        "Profil ko'rib chiqing yoki o'zaro simpatiyalaringizga o'ting."
    ),
    "profile_missing": "Profil topilmadi. Uni /start orqali yarating.",
    "profile_photo_error": "Eski fotografiya ochilmadi. «Фото» orqali yangisini yuklang.",
    "profile_status_active": "<b>Profil holati:</b> faol",
    "profile_status_hidden": "<b>Profil holati:</b> yashirilgan",
    "location_set": "belgilangan",
    "location_unset": "belgilanmagan",
    "search_settings": (
        "<b>⚙️ Qidiruv sozlamalari</b>\nYosh: {min_age}–{max_age}\nGeolokatsiya: {location}"
    ),
    "age_search": "Qidiruv uchun yosh",
    "change_location": "📍 Geolokatsiyani o'zgartirish",
    "seeking_label": "Qimani izlayapman",
    "back_menu": "🏠 Menyuga",
    "profile_saved": "<b>Tayyor!</b> Profil yangilandi 💜",
    "next": "Keyingi ➡️",
    "like": "💜 Yoqdi",
    "undo": "⏪ Profilni qaytarish",
    "block": "🚫 Bloklash",
    "report": "⚠️ Shikoyat qilish",
    "open_contact": "💬 Kontaktni ochish",
    "view_likes": "💌 Like'larni ko'rish",
    "view_profile": "💜 Profilni ko'rish",
    "send_location": "📍 Geolokatsiya yuborish",
    "send_location_placeholder": "Geolokatsiyani yuboring 📍",
    "edit_name": "<b>Yangi ism</b>\n2–40 belgidan iborat ism yuboring.",
    "edit_age": "<b>Yangi yosh</b>\n18–99 oralig‘ida butun son yuboring.",
    "edit_city": "<b>Yangi shahar</b>\n2–60 belgidan iborat shahar nomini yuboring.",
    "edit_bio": "<b>Yangi tavsif</b>\n300 tagacha belgi yuboring.",
    "edit_gender": "<b>Jinsni tanlang</b>",
    "edit_seeking": "<b>Qimani izlayapsiz?</b>",
    "edit_location": "<b>Yangi joylashuv 📍</b>\nQuyidagi tugma orqali geolokatsiya yuboring.",
    "edit_photo": "<b>Yangi foto</b>\nBitta foto shaklida yuboring.",
    "age_search_prompt": "<b>Qidiruv uchun yosh</b>\nMinimal va maksimal yoshni probel bilan yuboring, masalan: 20 35.",  # noqa: E501
    "profile_visible": "<b>Profil yana ko‘rinadi 💜</b>\nEndi uni boshqa foydalanuvchilar ko‘radi.",
    "profile_hidden": "<b>Profil yashirildi</b>\nYangi foydalanuvchilar uni qidiruvda ko‘rmaydi.",
    "search_saved": "<b>Tayyor!</b> Qidiruv sozlamalari saqlandi 💜",
    "access_restricted": "<b>Kirish cheklangan</b>\n/help, /privacy, /id va /delete dan foydalanishingiz mumkin.",  # noqa: E501
    "pass": "Keyingi ➡️",
    "return_profile": "Profilni qaytarish",
    "block_profile": "Bloklash",
    "report_profile": "Shikoyat qilish",
    "open_contact_short": "Kontaktni ochish",
    "matches_short": "O'zaro simpatiyalar",
    "matches_title_page": "<b>✨ O'zaro simpatiyalar</b>\nSahifa {page}",
    "no_matches": "<b>Hozircha o'zaro simpatiya yo‘q 💜</b>\nProfil ko‘rib chiqing — bir like bilan tanishuv boshlanishi mumkin.",  # noqa: E501
    "name": "Ism",
    "age": "Yosh",
    "gender": "Jins",
    "seeking": "Qimani izlayapman",
    "location": "Joylashuv",
    "bio": "Tavsif",
    "photo": "Foto",
    "hide_profile": "Profilni yashirish",
    "show_profile": "Profilni ko'rsatish",
    "delete_profile": "Profilni o'chirish",
    "male": "Erkak",
    "female": "Ayol",
    "any": "Muhim emas",
}
_EN: Final = {
    "menu_discover": "💜 Browse profiles",
    "menu_profile": "👤 My profile",
    "menu_likes": "💌 Likes",
    "menu_matches": "✨ Matches",
    "menu_settings": "⚙️ Settings",
    "menu_premium": "💎 Premium",
    "menu_help": "❔ Help",
    "menu_placeholder": "Choose an action 💜",
    "home": "<b>💜 Great to see you!</b>\nBrowse profiles or check your matches.",
    "profile_missing": "Profile not found. Create it with /start.",
    "profile_photo_error": "Could not open the previous photo. Upload a new one from Photo.",
    "profile_status_active": "<b>Profile status:</b> active",
    "profile_status_hidden": "<b>Profile status:</b> hidden",
    "location_set": "set",
    "location_unset": "not set",
    "search_settings": "<b>⚙️ Search settings</b>\nAge: {min_age}–{max_age}\nLocation: {location}",
    "age_search": "Search age",
    "change_location": "📍 Change location",
    "seeking_label": "Looking for",
    "back_menu": "🏠 Menu",
    "profile_saved": "<b>Done!</b> Profile updated 💜",
    "age_search_prompt": "<b>Search age</b>\nSend the minimum and maximum age separated by a space, for example: 20 35.",  # noqa: E501
    "profile_visible": "<b>Profile is visible again 💜</b>\nOther users can see it now.",
    "profile_hidden": "<b>Profile hidden</b>\nNew users will not see it in search.",
    "search_saved": "<b>Done!</b> Search settings saved 💜",
    "access_restricted": "<b>Access restricted</b>\nYou can use /help, /privacy, /id and /delete.",
    "next": "Next ➡️",
    "like": "💜 Like",
    "undo": "⏪ Return profile",
    "block": "🚫 Block",
    "report": "⚠️ Report",
    "open_contact": "💬 Open contact",
    "view_likes": "💌 View likes",
    "view_profile": "💜 View profile",
    "send_location": "📍 Send location",
    "send_location_placeholder": "Send your location 📍",
    "edit_name": "<b>New name</b>\nSend 2–40 characters.",
    "edit_age": "<b>New age</b>\nSend a whole number from 18 to 99.",
    "edit_city": "<b>New city</b>\nSend a city name of 2–60 characters.",
    "edit_bio": "<b>New bio</b>\nSend up to 300 characters.",
    "edit_gender": "<b>Choose gender</b>",
    "edit_seeking": "<b>Who are you looking for?</b>",
    "edit_location": "<b>New location 📍</b>\nSend location using the button below.",
    "edit_photo": "<b>New photo</b>\nSend one photo.",
    "pass": "Next ➡️",
    "return_profile": "Return profile",
    "block_profile": "Block",
    "report_profile": "Report",
    "open_contact_short": "Open contact",
    "matches_short": "Matches",
    "matches_title_page": "<b>✨ Matches</b>\nPage {page}",
    "no_matches": "<b>No matches yet 💜</b>\nBrowse profiles — a mutual connection can start with one like.",  # noqa: E501
    "name": "Name",
    "age": "Age",
    "gender": "Gender",
    "seeking": "Looking for",
    "location": "Location",
    "bio": "Bio",
    "photo": "Photo",
    "hide_profile": "Hide profile",
    "show_profile": "Show profile",
    "delete_profile": "Delete profile",
    "male": "Man",
    "female": "Woman",
    "any": "Any",
}
_UZ.update(
    {
        "send_location": "📍 Geolokatsiya yuborish",
        "send_location_placeholder": "Geolokatsiyani yuboring 📍",
        "edit_name": "<b>Yangi ism</b>\n2–40 belgidan iborat ism yuboring.",
        "edit_age": "<b>Yangi yosh</b>\n18–99 oralig‘ida butun son yuboring.",
        "edit_city": "<b>Yangi shahar</b>\n2–60 belgidan iborat shahar nomini yuboring.",
        "edit_bio": "<b>Yangi tavsif</b>\n300 tagacha belgi yuboring.",
        "edit_gender": "<b>Jinsni tanlang</b>",
        "edit_seeking": "<b>Qimani izlayapsiz?</b>",
        "edit_location": "<b>Yangi joylashuv 📍</b>\nQuyidagi tugma orqali geolokatsiya yuboring.",
        "edit_photo": "<b>Yangi foto</b>\nBitta foto shaklida yuboring.",
    }
)
_EN.update(
    {
        "send_location": "📍 Send location",
        "send_location_placeholder": "Send your location 📍",
        "edit_name": "<b>New name</b>\nSend 2–40 characters.",
        "edit_age": "<b>New age</b>\nSend a whole number from 18 to 99.",
        "edit_city": "<b>New city</b>\nSend a city name of 2–60 characters.",
        "edit_bio": "<b>New bio</b>\nSend up to 300 characters.",
        "edit_gender": "<b>Choose gender</b>",
        "edit_seeking": "<b>Who are you looking for?</b>",
        "edit_location": "<b>New location 📍</b>\nSend location using the button below.",
        "edit_photo": "<b>New photo</b>\nSend one photo.",
    }
)
TRANSLATIONS: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "welcome": (
            "<b>👋 Привет!</b>\n\n🌍 <b>Рядом</b> — здесь можно найти новые знакомства.\n\n"
            "Выбери язык, чтобы продолжить:"
        ),
        "language_selected": "<b>🌐 Язык выбран: Русский</b>\n\nПриятного общения!",
        "continue": "Продолжить",
        **_COMMON,
    },
    "uz": {
        "welcome": (
            "<b>👋 Xush kelibsiz!</b>\n\n🌍 <b>Рядом</b> — bu yerda yangi tanishuvlarni "
            "topishingiz mumkin.\n\nDavom etish uchun tilni tanlang:"
        ),
        "language_selected": "<b>🌐 Til tanlandi: O‘zbekcha</b>\n\nYaxshi muloqotlar!",
        "continue": "Davom etish",
        **_UZ,
    },
    "en": {
        "welcome": (
            "<b>👋 Welcome!</b>\n\n🌍 <b>Рядом</b> — meet new people here.\n\n"
            "Choose your language to continue:"
        ),
        "language_selected": "<b>🌐 Language selected: English</b>\n\nHave a great experience!",
        "continue": "Continue",
        **_EN,
    },
}


def normalize_language(language: str | None) -> str:
    value = (language or "").strip().lower()
    return value if value in LANGUAGES else DEFAULT_LANGUAGE


def tr(key: str, language: str | None = None, **format_values: object) -> str:
    language = normalize_language(language or current_language.get())
    value = TRANSLATIONS[language].get(key, TRANSLATIONS[DEFAULT_LANGUAGE][key])
    return value.format(**format_values) if format_values else value
