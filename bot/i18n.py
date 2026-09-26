from __future__ import annotations

from contextvars import ContextVar
from typing import Final

LANGUAGES: Final = ("ru", "uz", "en", "kg")
DEFAULT_LANGUAGE: Final = "ru"
current_language: ContextVar[str | None] = ContextVar("current_language", default=None)
LANGUAGE_NAMES: Final = {
    "uz": "🇺🇿 O'zbekcha",
    "ru": "🇷🇺 Русский",
    "en": "🇬🇧 English",
    "kg": "🇰🇬 Кыргызча",
}

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
    "change_language": "🌐 Изменить язык",
    "premium_settings": "⚙️ Premium настройки",
    "premium_home": "🏠 В меню",
    "premium_try": "Попробовать",
    "premium_other": "💎 Другой тариф",
    "premium_terms": "📄 Условия покупки",
    "premium_accept": "✅ Принимаю условия и оплачиваю",
    "plan_3d": "3 дня",
    "plan_1m": "1 месяц",
    "plan_3m": "3 месяца",
    "stale_button": "Кнопка устарела или недействительна. Продолжи с помощью /start.",
    "unknown_message": "Выбери пункт меню или отправь /start. /cancel — отмена.",
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
    "change_language": "🌐 Tilni o‘zgartirish",
    "premium_settings": "⚙️ Premium sozlamalari",
    "premium_home": "🏠 Menyuga",
    "premium_try": "Sinab ko‘rish",
    "premium_other": "💎 Boshqa tarif",
    "premium_terms": "📄 Xarid shartlari",
    "premium_accept": "✅ Shartlarni qabul qilaman va to‘layman",
    "plan_3d": "3 kun",
    "plan_1m": "1 oy",
    "plan_3m": "3 oy",
    "stale_button": "Tugma eskirgan yoki amalga oshmaydi. /start orqali davom eting.",
    "unknown_message": "Menyudan biror amalni tanlang yoki /start yuboring. /cancel — bekor qilish.",  # noqa: E501
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
    "change_language": "🌐 Change language",
    "premium_settings": "⚙️ Premium settings",
    "premium_home": "🏠 Menu",
    "premium_try": "Try it",
    "premium_other": "💎 Another plan",
    "premium_terms": "📄 Purchase terms",
    "premium_accept": "✅ Accept terms and pay",
    "plan_3d": "3 days",
    "plan_1m": "1 month",
    "plan_3m": "3 months",
    "stale_button": "This button is outdated or invalid. Continue with /start.",
    "unknown_message": "Choose a menu action or send /start. /cancel — cancel.",
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
_RU_EXTRA: Final = {
    "caption_distance": "📍 {distance} км от тебя",
    "caption_city": "📍 {city}",
    "caption_no_location": "📍 Геолокация",
    "location_city_default": "Геолокация",
    "match_notify": (
        "<b>У вас взаимная симпатия! 💜</b>\n\n"
        "Открой контакт, чтобы познакомиться поближе."
    ),
    "like_notify": (
        "<b>💌 Кому-то понравилась твоя анкета</b>\n\n"
        "Посмотри входящие лайки — возможно, симпатия взаимна."
    ),
    "temporary_error": "Не получилось выполнить действие. Попробуй ещё раз чуть позже 💜",
    "message_send_failed": (
        "Не получилось отправить сообщение или фото. Попробуй ещё раз. "
        "Если фото устарело, обнови его в разделе «Моя анкета»."
    ),
    "cancel_done": "Действие отменено. Сохранённая анкета не изменилась.",
    "own_id": "Твой Telegram ID: <code>{telegram_id}</code>",
    "delete_confirm": "Да, удалить",
    "delete_cancel": "Отмена",
    "delete_stale": "Подтверждение устарело. Начни заново с /delete.",
    "delete_done": (
        "<b>Анкета удалена</b>\n"
        "Связанные реакции и взаимные симпатии удалены. Записи модерации сохранены."
    ),
    "err_banned": "Твой доступ ограничен. Доступны /help, /privacy и /delete.",
    "err_rate_limit": "Подожди секунду и нажми снова.",
}
_UZ.update(
    {
        "caption_distance": "📍 sendan {distance} km",
        "caption_city": "📍 {city}",
        "caption_no_location": "📍 Geolokatsiya",
        "location_city_default": "Geolokatsiya",
        "match_notify": (
            "<b>Sizda o'zaro simpatiya bor! 💜</b>\n\n"
            "Yaqinroq tanishish uchun kontaktni oching."
        ),
        "like_notify": (
            "<b>💌 Kimdir profilingizni yoqtirdi</b>\n\n"
            "Kiruvchi like'larni ko'ring — balki simpatiya o'zaro."
        ),
        "temporary_error": "Amalni bajarib bo'lmadi. Birozdan so'ng qayta urinib ko'ring 💜",
        "message_send_failed": (
            "Xabar yoki fotoni yuborib bo'lmadi. Qayta urinib ko'ring. "
            "Foto eskirgan bo'lsa, «Mening profilim» bo'limida yangilang."
        ),
        "cancel_done": "Amal bekor qilindi. Saqlangan profil o'zgarmadi.",
        "own_id": "Telegram ID'ingiz: <code>{telegram_id}</code>",
        "delete_confirm": "Ha, o'chirish",
        "delete_cancel": "Bekor qilish",
        "delete_stale": "Tasdiqlash eskirgan. /delete bilan qaytadan boshlang.",
        "delete_done": (
            "<b>Profil o'chirildi</b>\n"
            "Tegishli reaksiyalar va o'zaro simpatiyalar o'chirildi. "
            "Moderatsiya yozuvlari saqlandi."
        ),
        "err_banned": "Kirishingiz cheklangan. /help, /privacy va /delete mavjud.",
        "err_rate_limit": "Bir soniya kutib, qayta bosing.",
    }
)
_EN.update(
    {
        "caption_distance": "📍 {distance} km away",
        "caption_city": "📍 {city}",
        "caption_no_location": "📍 Location",
        "location_city_default": "Location",
        "match_notify": (
            "<b>It's a match! 💜</b>\n\n"
            "Open the contact to get to know each other."
        ),
        "like_notify": (
            "<b>💌 Someone liked your profile</b>\n\n"
            "Check your incoming likes — the feeling may be mutual."
        ),
        "temporary_error": "Could not complete the action. Try again a little later 💜",
        "message_send_failed": (
            "Could not send the message or photo. Try again. "
            "If the photo is outdated, update it in My profile."
        ),
        "cancel_done": "Action cancelled. Your saved profile was not changed.",
        "own_id": "Your Telegram ID: <code>{telegram_id}</code>",
        "delete_confirm": "Yes, delete",
        "delete_cancel": "Cancel",
        "delete_stale": "This confirmation has expired. Start again with /delete.",
        "delete_done": (
            "<b>Profile deleted</b>\n"
            "Related reactions and matches were deleted. Moderation records are kept."
        ),
        "err_banned": "Your access is restricted. /help, /privacy and /delete are available.",
        "err_rate_limit": "Wait a second and tap again.",
    }
)

_RU_EXTRA.update(
    {
        "reg_adult_button": "Мне уже есть 18 лет",
        "reg_consent_button": "Согласен / согласна",
        "reg_retry_username": "Проверить ещё раз",
        "reg_name_prompt": (
            "<b>Как тебя зовут?</b>\n"
            "Напиши имя для анкеты: от 2 до 40 символов.\n\n"
            "<i>Без контактов и ссылок. /cancel — отмена.</i>"
        ),
        "reg_age_prompt": "<b>Сколько тебе лет?</b>\nОтправь возраст целым числом от 18 до 99.",
        "reg_gender_prompt": "<b>Укажи свой пол</b>",
        "reg_seeking_prompt": "<b>Кого ты ищешь?</b>",
        "reg_location_prompt": (
            "<b>Где ты находишься? 📍</b>\n"
            "Отправь геолокацию кнопкой ниже. Сначала покажем людей ближе к тебе, "
            "затем — тех, кто дальше.\n\n"
            "<i>Точные координаты другим пользователям не показываются.</i>"
        ),
    }
)
_UZ.update(
    {
        "reg_adult_button": "Men 18 yoshdaman",
        "reg_consent_button": "Roziman",
        "reg_retry_username": "Yana bir bor tekshirish",
        "reg_name_prompt": (
            "<b>Ismingiz nima?</b>\n"
            "Profil uchun ism yozing: 2–40 belgi.\n\n"
            "<i>Kontakt va havolalarsiz. /cancel — bekor qilish.</i>"
        ),
        "reg_age_prompt": (
            "<b>Yoshingiz nechada?</b>\nYoshni 18–99 oralig'ida butun son sifatida yuboring."
        ),
        "reg_gender_prompt": "<b>Jinsingizni ko'rsating</b>",
        "reg_seeking_prompt": "<b>Qimani izlayapsiz?</b>",
        "reg_location_prompt": (
            "<b>Qayerdasiz? 📍</b>\n"
            "Quyidagi tugma orqali geolokatsiya yuboring. Avval sizga yaqinroq odamlarni, "
            "keyin uzoqroqlarni ko'rsatamiz.\n\n"
            "<i>Aniq koordinatalar boshqalarga ko'rsatilmaydi.</i>"
        ),
    }
)
_EN.update(
    {
        "reg_adult_button": "I am over 18",
        "reg_consent_button": "I agree",
        "reg_retry_username": "Check again",
        "reg_name_prompt": (
            "<b>What is your name?</b>\n"
            "Write a name for your profile: 2 to 40 characters.\n\n"
            "<i>No contacts or links. /cancel — cancel.</i>"
        ),
        "reg_age_prompt": "<b>How old are you?</b>\nSend your age as a whole number from 18 to 99.",
        "reg_gender_prompt": "<b>Choose your gender</b>",
        "reg_seeking_prompt": "<b>Who are you looking for?</b>",
        "reg_location_prompt": (
            "<b>Where are you? 📍</b>\n"
            "Send your location with the button below. We show people closer to you "
            "first, then those further away.\n\n"
            "<i>Exact coordinates are not shown to other users.</i>"
        ),
    }
)

_RU_EXTRA.update(
    {
        "reg_bio_prompt": (
            "<b>Расскажи о себе</b>\n"
            "Напиши до 300 символов или пропусти этот шаг.\n\n"
            "<i>Не указывай @username и ссылки.</i>"
        ),
        "reg_skip_button": "Пропустить",
        "reg_photo_prompt": (
            "<b>Добавь фотографию</b>\n"
            "Отправь одно своё фото как фотографию в Telegram.\n\n"
            "<i>Файл или видео не подойдут.</i>"
        ),
        "reg_confirm_button": "Подтвердить",
        "reg_restart_button": "Заполнить заново",
        "reg_done": (
            "<b>Готово! Анкета создана 💜</b>\n"
            "Поиск настроен на возраст 18–99 лет. Анкеты будут показаны от ближайших "
            "к более дальним. Геолокацию можно изменить в настройках."
        ),
        "reg_wrong_photo": (
            "Отправь одну фотографию как фото. Видео, файл и текст не подойдут.\n\n"
            "<i>/cancel — отмена.</i>"
        ),
        "reg_wrong_input": (
            "Ответь на текущий вопрос или нажми подходящую кнопку. "
            "/cancel — отмена, /start — начать заново."
        ),
    }
)
_UZ.update(
    {
        "reg_bio_prompt": (
            "<b>O'zingiz haqingizda yozing</b>\n"
            "300 tagacha belgi yozing yoki bu qadamni o'tkazib yuboring.\n\n"
            "<i>@username va havolalarni ko'rsatmang.</i>"
        ),
        "reg_skip_button": "O'tkazib yuborish",
        "reg_photo_prompt": (
            "<b>Foto qo'shing</b>\n"
            "Bitta o'z fotongizni Telegram'da foto sifatida yuboring.\n\n"
            "<i>Fayl yoki video mos kelmaydi.</i>"
        ),
        "reg_confirm_button": "Tasdiqlash",
        "reg_restart_button": "Qaytadan to'ldirish",
        "reg_done": (
            "<b>Tayyor! Profil yaratildi 💜</b>\n"
            "Qidiruv 18–99 yosh uchun sozlandi. Profillar avval yaqinroqlardan boshlab "
            "ko'rsatiladi. Geolokatsiyani sozlamalarda o'zgartirish mumkin."
        ),
        "reg_wrong_photo": (
            "Bitta fotoni foto sifatida yuboring. Video, fayl va matn mos kelmaydi.\n\n"
            "<i>/cancel — bekor qilish.</i>"
        ),
        "reg_wrong_input": (
            "Joriy savolga javob bering yoki mos tugmani bosing. "
            "/cancel — bekor qilish, /start — qaytadan boshlash."
        ),
    }
)
_EN.update(
    {
        "reg_bio_prompt": (
            "<b>Tell us about yourself</b>\n"
            "Write up to 300 characters or skip this step.\n\n"
            "<i>Do not include @username or links.</i>"
        ),
        "reg_skip_button": "Skip",
        "reg_photo_prompt": (
            "<b>Add a photo</b>\n"
            "Send one of your own photos as a photo in Telegram.\n\n"
            "<i>A file or video will not work.</i>"
        ),
        "reg_confirm_button": "Confirm",
        "reg_restart_button": "Fill in again",
        "reg_done": (
            "<b>Done! Profile created 💜</b>\n"
            "Search is set to ages 18–99. Profiles are shown from the nearest to the "
            "furthest. You can change your location in settings."
        ),
        "reg_wrong_photo": (
            "Send one picture as a photo. Video, files and text will not work.\n\n"
            "<i>/cancel — cancel.</i>"
        ),
        "reg_wrong_input": (
            "Answer the current question or tap a matching button. "
            "/cancel — cancel, /start — start over."
        ),
    }
)

_RU_EXTRA.update(
    {
        "intro": (
            "<b>💜 Рядом</b>\n"
            "Твоя история начинается с одного знакомства.\n\n"
            "Создай анкету, смотри людей рядом и находи взаимную симпатию.\n\n"
            "<i>Только для пользователей старше 18 лет. Возраст указывается самостоятельно; "
            "документы не проверяются.</i>"
        ),
        "consent": (
            "<b>Согласие и приватность</b>\n\n"
            "После подтверждения твою анкету — имя, возраст, пол, описание и фото — "
            "увидят другие пользователи. После взаимной симпатии участник сможет открыть "
            "твой Telegram username. Геолокация нужна только для расчёта расстояния и другим "
            "не показывается.\n\n"
            "Бот не запрашивает телефон, пароль, паспорт или точный адрес. Не указывай "
            "@username и ссылки в имени или описании. Подробнее: /privacy.\n\n"
            "<b>Ты согласен или согласна?</b>"
        ),
        "username_help": (
            "<b>Добавь Telegram username</b>\n\n"
            "Открой Telegram → Настройки → Изменить профиль → Имя пользователя. "
            "Затем вернись сюда и нажми «Проверить ещё раз».\n\n"
            "<i>Не отправляй username в этот чат.</i>"
        ),
    }
)
_UZ.update(
    {
        "intro": (
            "<b>💜 Рядом</b>\n"
            "Sizning hikoyangiz bitta tanishuvdan boshlanadi.\n\n"
            "Profil yarating, yaqin atrofdagi odamlarni ko'ring va o'zaro simpatiyani toping.\n\n"
            "<i>Faqat 18 yoshdan katta foydalanuvchilar uchun. Yosh mustaqil ko'rsatiladi; "
            "hujjatlar tekshirilmaydi.</i>"
        ),
        "consent": (
            "<b>Rozilik va maxfiylik</b>\n\n"
            "Tasdiqlaganingizdan so'ng profilingizni — ism, yosh, jins, tavsif va foto — "
            "boshqa foydalanuvchilar ko'radi. O'zaro simpatiyadan keyin foydalanuvchi "
            "Telegram username'ingizni ochishi mumkin. Geolokatsiya faqat masofani hisoblash "
            "uchun kerak va boshqalarga ko'rsatilmaydi.\n\n"
            "Bot telefon, parol, pasport yoki aniq manzilni so'ramaydi. Ism yoki tavsifda "
            "@username va havolalarni ko'rsatmang. Batafsil: /privacy.\n\n"
            "<b>Rozimisiz?</b>"
        ),
        "username_help": (
            "<b>Telegram username qo'shing</b>\n\n"
            "Telegram → Sozlamalar → Profilni o'zgartirish → Foydalanuvchi nomi bo'limini "
            "oching. Keyin bu yerga qaytib «Yana bir bor tekshirish» tugmasini bosing.\n\n"
            "<i>Username'ni bu chatga yubormang.</i>"
        ),
    }
)
_EN.update(
    {
        "intro": (
            "<b>💜 Рядом</b>\n"
            "Your story starts with one meeting.\n\n"
            "Create a profile, browse people nearby and find a mutual connection.\n\n"
            "<i>For users over 18 only. Age is self-declared; documents are not verified.</i>"
        ),
        "consent": (
            "<b>Consent and privacy</b>\n\n"
            "After confirmation, other users will see your profile — name, age, gender, "
            "description and photo. After a mutual match, the other person can open your "
            "Telegram username. Location is used only to calculate distance and is not "
            "shown to others.\n\n"
            "The bot never asks for your phone, password, passport or exact address. Do not "
            "put @username or links in your name or description. Details: /privacy.\n\n"
            "<b>Do you agree?</b>"
        ),
        "username_help": (
            "<b>Add a Telegram username</b>\n\n"
            "Open Telegram → Settings → Edit profile → Username. Then come back here and "
            "tap Check again.\n\n"
            "<i>Do not send your username to this chat.</i>"
        ),
    }
)

_RU_EXTRA.update(
    {
        "help": (
            "<b>❔ Помощь</b>\n\n"
            "Смотри анкеты, ставь 💜 и при взаимной симпатии открывай контакт. "
            "Общение продолжится в личном чате Telegram — анонимного чата в боте нет.\n\n"
            "Бот только для людей старше 18 лет. Спам, поддельные анкеты и недопустимый "
            "контент запрещены. Подозрительную анкету можно заблокировать или отправить "
            "жалобу. Не передавай пароли, деньги или документы.\n\n"
            "/start — меню или регистрация\n"
            "/privacy — конфиденциальность\n"
            "/cancel — отмена текущего действия\n"
            "/id — твой Telegram ID\n"
            "/delete — удаление анкеты\n\n"
            "<i>Незавершённая анкета может исчезнуть после перезапуска; готовая анкета "
            "сохранится.</i>"
        ),
    }
)
_UZ.update(
    {
        "help": (
            "<b>❔ Yordam</b>\n\n"
            "Profillarni ko'ring, 💜 bosing va o'zaro simpatiyada kontaktni oching. "
            "Muloqot Telegram shaxsiy chatida davom etadi — botda anonim chat yo'q.\n\n"
            "Bot faqat 18 yoshdan katta odamlar uchun. Spam, soxta profillar va nojoiz "
            "kontent taqiqlanadi. Shubhali profilni bloklashingiz yoki shikoyat yuborishingiz "
            "mumkin. Parol, pul yoki hujjatlarni bermang.\n\n"
            "/start — menyu yoki ro'yxatdan o'tish\n"
            "/privacy — maxfiylik\n"
            "/cancel — joriy amalni bekor qilish\n"
            "/id — Telegram ID'ingiz\n"
            "/delete — profilni o'chirish\n\n"
            "<i>Yakunlanmagan profil qayta ishga tushgandan so'ng yo'qolishi mumkin; tayyor "
            "profil saqlanadi.</i>"
        ),
    }
)
_EN.update(
    {
        "help": (
            "<b>❔ Help</b>\n\n"
            "Browse profiles, tap 💜 and open the contact on a mutual match. Chatting "
            "continues in a private Telegram chat — there is no anonymous chat in the bot.\n\n"
            "The bot is for people over 18 only. Spam, fake profiles and unacceptable "
            "content are forbidden. You can block a suspicious profile or send a report. "
            "Never share passwords, money or documents.\n\n"
            "/start — menu or registration\n"
            "/privacy — privacy\n"
            "/cancel — cancel the current action\n"
            "/id — your Telegram ID\n"
            "/delete — delete your profile\n\n"
            "<i>An unfinished profile may be lost after a restart; a saved profile is "
            "kept.</i>"
        ),
    }
)

_RU_EXTRA.update(
    {
        "privacy": (
            "<b>🔐 Конфиденциальность</b>\n\n"
            "Анкета становится видна только после подтверждения. Бот хранит Telegram ID, "
            "username, анкету, координаты, настройки поиска, время согласия, решения, "
            "взаимные симпатии, блокировки и жалобы. Хранится file_id фото; само фото на диск "
            "сервера не загружается. Геолокация используется для сортировки по расстоянию и "
            "не показывается другим. Контакт открывается только при взаимной симпатии.\n\n"
            "Скрытие анкеты останавливает новый поиск и получение лайков; прежние взаимные "
            "симпатии сохраняются. Блокировка ограничивает видимость и доступ к контакту в "
            "боте, но не блокирует личный чат Telegram. Жалобы видят администраторы; автор "
            "жалобы не раскрывается. Администратор может просматривать жалобы и текущую "
            "анкету, а также блокировать пользователей.\n\n"
            "Удаление: /delete.\n\n"
        ),
    }
)
_UZ.update(
    {
        "privacy": (
            "<b>🔐 Maxfiylik</b>\n\n"
            "Profil faqat tasdiqlangandan so'ng ko'rinadi. Bot Telegram ID, username, profil, "
            "koordinatalar, qidiruv sozlamalari, rozilik vaqti, qarorlar, o'zaro simpatiyalar, "
            "bloklashlar va shikoyatlarni saqlaydi. Foto file_id saqlanadi; fotoning o'zi server "
            "diskiga yuklanmaydi. Geolokatsiya masofa bo'yicha saralash uchun ishlatiladi va "
            "boshqalarga ko'rsatilmaydi. Kontakt faqat o'zaro simpatiyada ochiladi.\n\n"
            "Profilni yashirish yangi qidiruv va like olishni to'xtatadi; avvalgi o'zaro "
            "simpatiyalar saqlanadi. Bloklash botda ko'rinish va kontaktni cheklaydi, ammo "
            "Telegram shaxsiy chatini bloklamaydi. Shikoyatlarni administratorlar ko'radi; "
            "shikoyat muallifi oshkor qilinmaydi. Administrator shikoyatlarni va joriy profilni "
            "ko'rishi, foydalanuvchilarni bloklashi mumkin.\n\n"
            "O'chirish: /delete.\n\n"
        ),
    }
)
_EN.update(
    {
        "privacy": (
            "<b>🔐 Privacy</b>\n\n"
            "Your profile becomes visible only after confirmation. The bot stores your "
            "Telegram ID, username, profile, coordinates, search settings, consent time, "
            "decisions, matches, blocks and reports. Photo file_id is stored; the photo itself "
            "is not downloaded to the server disk. Location is used to sort by distance and is "
            "not shown to others. A contact opens only on a mutual match.\n\n"
            "Hiding the profile stops new search and likes; previous matches are kept. A block "
            "limits visibility and access to the contact in the bot, but does not block the "
            "private Telegram chat. Administrators see reports; the reporter is not revealed. "
            "An administrator can review reports and the current profile and block users.\n\n"
            "Deletion: /delete.\n\n"
        ),
    }
)

_RU_EXTRA.update(
    {
        "delete_notice": (
            "<b>🗑 Удаление анкеты</b>\n\n"
            "Будут удалены имя, возраст, пол, геолокация, описание, file_id фото, настройки "
            "поиска, время согласия и создания анкеты, связанные реакции и взаимные симпатии. "
            "Сохранённый username также будет очищен.\n\n"
            "Для модерации сохранятся внутренний ID, Telegram ID, статус блокировки, время "
            "создания аккаунта, записи о блокировках — ID обеих сторон и время — и жалобах — "
            "ID обеих сторон, причина или комментарий, статус, время и ID проверившего "
            "администратора. Актуальный username может обновиться при следующем сообщении. "
            "Старые сообщения Telegram и уже открытые контакты отозвать нельзя.\n\n"
            "<b>Точно удалить анкету?</b>"
        ),
    }
)
_UZ.update(
    {
        "delete_notice": (
            "<b>🗑 Profilni o'chirish</b>\n\n"
            "Ism, yosh, jins, geolokatsiya, tavsif, foto file_id, qidiruv sozlamalari, "
            "rozilik va profil yaratilgan vaqt, tegishli reaksiyalar va o'zaro simpatiyalar "
            "o'chiriladi. Saqlangan username ham tozalanadi.\n\n"
            "Moderatsiya uchun ichki ID, Telegram ID, bloklash holati, akkaunt yaratilgan vaqt, "
            "bloklashlar — ikki tomon ID'si va vaqt — va shikoyatlar — ikki tomon ID'si, sabab "
            "yoki izoh, holat, vaqt va tekshirgan administrator ID'si — saqlanadi. Joriy username "
            "keyingi xabarda yangilanishi mumkin. Telegram'dagi eski xabarlar va allaqachon "
            "ochilgan kontaktlarni qaytarib bo'lmaydi.\n\n"
            "<b>Profilni aniq o'chirasizmi?</b>"
        ),
    }
)
_EN.update(
    {
        "delete_notice": (
            "<b>🗑 Deleting your profile</b>\n\n"
            "Name, age, gender, location, description, photo file_id, search settings, consent "
            "and profile creation time, related reactions and matches will be deleted. The "
            "stored username is cleared as well.\n\n"
            "For moderation the bot keeps the internal ID, Telegram ID, block status, account "
            "creation time, block records — both user IDs and time — and reports — both user "
            "IDs, reason or comment, status, time and the reviewing administrator ID. The "
            "current username may be refreshed on the next message. Old Telegram messages and "
            "already opened contacts cannot be recalled.\n\n"
            "<b>Delete the profile for sure?</b>"
        ),
    }
)

_RU_EXTRA.update(
    {
        "err_invalid_button": "Кнопка устарела или недействительна.",
        "err_profile_not_found": "Анкета не найдена.",
        "err_profile_not_found_start": "Анкета не найдена. Отправь /start.",
        "err_profile_deleted": "Анкета удалена.",
        "err_create_profile": "Сначала создай анкету с помощью /start.",
        "err_two_ints": "Отправь два целых числа, например: 20 35.",
        "err_ints_expected": "Возраст должен быть указан двумя целыми числами, например: 20 35.",
        "err_send_text_or_cancel": "Отправь текст или используй /cancel.",
        "err_use_buttons_above": "Выбери вариант с помощью кнопок выше.",
        "err_button_unavailable": "Эта кнопка сейчас недоступна.",
        "err_profile_field_missing": "Анкета или поле не найдены.",
        "err_location_button": "Отправь геолокацию с помощью кнопки ниже.",
        "err_one_photo_photo": "Отправь одну фотографию как фото, а не файл или видео.",
        "err_message_unavailable": "Сообщение недоступно.",
        "err_invalid_command": "Некорректная команда.",
        "err_choose_reason": "Выбери причину с помощью кнопки.",
        "err_comment_length": "Комментарий должен содержать 1–300 символов.",
    }
)
_UZ.update(
    {
        "err_invalid_button": "Tugma eskirgan yoki yaroqsiz.",
        "err_profile_not_found": "Profil topilmadi.",
        "err_profile_not_found_start": "Profil topilmadi. /start yuboring.",
        "err_profile_deleted": "Profil o'chirilgan.",
        "err_create_profile": "Avval /start orqali profil yarating.",
        "err_two_ints": "Ikkita butun son yuboring, masalan: 20 35.",
        "err_ints_expected": "Yosh ikkita butun son bilan ko'rsatilishi kerak, masalan: 20 35.",
        "err_send_text_or_cancel": "Matn yuboring yoki /cancel dan foydalaning.",
        "err_use_buttons_above": "Yuqoridagi tugmalar orqali variantni tanlang.",
        "err_button_unavailable": "Bu tugma hozir mavjud emas.",
        "err_profile_field_missing": "Profil yoki maydon topilmadi.",
        "err_location_button": "Quyidagi tugma orqali geolokatsiya yuboring.",
        "err_one_photo_photo": "Bitta fotoni foto sifatida yuboring, fayl yoki video emas.",
        "err_message_unavailable": "Xabar mavjud emas.",
        "err_invalid_command": "Buyruq noto'g'ri.",
        "err_choose_reason": "Sababni tugma orqali tanlang.",
        "err_comment_length": "Izoh 1–300 belgidan iborat bo'lishi kerak.",
    }
)
_EN.update(
    {
        "err_invalid_button": "This button is outdated or invalid.",
        "err_profile_not_found": "Profile not found.",
        "err_profile_not_found_start": "Profile not found. Send /start.",
        "err_profile_deleted": "The profile was deleted.",
        "err_create_profile": "Create a profile with /start first.",
        "err_two_ints": "Send two whole numbers, for example: 20 35.",
        "err_ints_expected": "Age must be given as two whole numbers, for example: 20 35.",
        "err_send_text_or_cancel": "Send text or use /cancel.",
        "err_use_buttons_above": "Choose an option with the buttons above.",
        "err_button_unavailable": "This button is not available right now.",
        "err_profile_field_missing": "Profile or field not found.",
        "err_location_button": "Send your location with the button below.",
        "err_one_photo_photo": "Send one photo as a photo, not a file or video.",
        "err_message_unavailable": "Message is unavailable.",
        "err_invalid_command": "Invalid command.",
        "err_choose_reason": "Choose a reason with the button.",
        "err_comment_length": "The comment must be 1–300 characters long.",
    }
)

_RU_EXTRA.update(
    {
        "edit_cancel_hint": "\n\n<i>/cancel — отменить без сохранения.</i>",
        "edit_clear_bio": "Очистить описание",
        "no_undo_profile": "Нет анкеты для возврата. Последняя анкета должна быть пропущена.",
        "photo_counter": "Фото {position}",
        "decision_saved": "Твоё решение по этой анкете уже сохранено.",
        "matches_prev": "← Назад",
        "matches_next": "Далее →",
        "contact_opened": (
            "<b>💬 Контакт открыт</b>\n{url}\n\n"
            "Общение продолжится в личном чате Telegram."
        ),
        "contact_unavailable": (
            "<b>Контакт пока недоступен</b>\n"
            "Попроси пользователя добавить Telegram username и попробуй ещё раз позже."
        ),
        "contact_retry": "Попробовать снова",
        "reason_spam": "Спам",
        "reason_fake": "Фальшивая анкета",
        "reason_content": "Недопустимый контент",
        "reason_other": "Другое",
        "reason_other_value": "Другое: {value}",
        "report_reason_prompt": (
            "<b>Почему ты хочешь пожаловаться?</b>\n"
            "Выбери причину ниже.\n\n<i>/cancel — отмена.</i>"
        ),
        "report_confirm_prompt": (
            "<b>Отправить жалобу?</b>\n"
            "Её увидят администраторы, а анкета будет заблокирована для тебя. "
            "Пользователь не узнает, кто отправил жалобу."
        ),
        "report_send": "Отправить жалобу",
        "report_comment_prompt": (
            "<b>Опиши причину</b>\n"
            "Напиши комментарий длиной от 1 до 300 символов.\n\n"
            "<i>/cancel — отмена.</i>"
        ),
        "report_saved": "<b>Жалоба сохранена</b>\nАнкета заблокирована для тебя.",
        "blocked_notice": (
            "<b>Пользователь заблокирован</b>\n"
            "Анкеты больше не будут видны друг другу в боте, а контакт станет недоступен.\n\n"
            "<i>В личном чате Telegram пользователя можно заблокировать отдельно.</i>"
        ),
    }
)
_UZ.update(
    {
        "edit_cancel_hint": "\n\n<i>/cancel — saqlamasdan bekor qilish.</i>",
        "edit_clear_bio": "Tavsifni tozalash",
        "no_undo_profile": (
            "Qaytarish uchun profil yo'q. Oxirgi profil o'tkazib yuborilgan bo'lishi kerak."
        ),
        "photo_counter": "Foto {position}",
        "decision_saved": "Bu profil bo'yicha qaroringiz allaqachon saqlangan.",
        "matches_prev": "← Orqaga",
        "matches_next": "Keyingi →",
        "contact_opened": (
            "<b>💬 Kontakt ochildi</b>\n{url}\n\n"
            "Muloqot Telegram shaxsiy chatida davom etadi."
        ),
        "contact_unavailable": (
            "<b>Kontakt hozircha mavjud emas</b>\n"
            "Foydalanuvchidan Telegram username qo'shishni so'rang va keyinroq qayta urinib "
            "ko'ring."
        ),
        "contact_retry": "Qayta urinish",
        "reason_spam": "Spam",
        "reason_fake": "Soxta profil",
        "reason_content": "Nojoiz kontent",
        "reason_other": "Boshqa",
        "reason_other_value": "Boshqa: {value}",
        "report_reason_prompt": (
            "<b>Nima uchun shikoyat qilmoqchisiz?</b>\n"
            "Quyidagi sababni tanlang.\n\n<i>/cancel — bekor qilish.</i>"
        ),
        "report_confirm_prompt": (
            "<b>Shikoyat yuborilsinmi?</b>\n"
            "Uni administratorlar ko'radi va profil siz uchun bloklanadi. "
            "Foydalanuvchi shikoyatni kim yuborganini bilmaydi."
        ),
        "report_send": "Shikoyat yuborish",
        "report_comment_prompt": (
            "<b>Sababni yozing</b>\n"
            "1–300 belgidan iborat izoh yozing.\n\n<i>/cancel — bekor qilish.</i>"
        ),
        "report_saved": "<b>Shikoyat saqlandi</b>\nProfil siz uchun bloklandi.",
        "blocked_notice": (
            "<b>Foydalanuvchi bloklandi</b>\n"
            "Profillar botda bir-biriga ko'rinmaydi va kontakt yopiladi.\n\n"
            "<i>Telegram shaxsiy chatida foydalanuvchini alohida bloklashingiz mumkin.</i>"
        ),
    }
)
_EN.update(
    {
        "edit_cancel_hint": "\n\n<i>/cancel — cancel without saving.</i>",
        "edit_clear_bio": "Clear description",
        "no_undo_profile": "No profile to return. The last profile must have been skipped.",
        "photo_counter": "Photo {position}",
        "decision_saved": "Your decision on this profile is already saved.",
        "matches_prev": "← Back",
        "matches_next": "Next →",
        "contact_opened": (
            "<b>💬 Contact opened</b>\n{url}\n\n"
            "Chatting continues in a private Telegram chat."
        ),
        "contact_unavailable": (
            "<b>Contact is not available yet</b>\n"
            "Ask the user to add a Telegram username and try again later."
        ),
        "contact_retry": "Try again",
        "reason_spam": "Spam",
        "reason_fake": "Fake profile",
        "reason_content": "Unacceptable content",
        "reason_other": "Other",
        "reason_other_value": "Other: {value}",
        "report_reason_prompt": (
            "<b>Why do you want to report?</b>\n"
            "Choose a reason below.\n\n<i>/cancel — cancel.</i>"
        ),
        "report_confirm_prompt": (
            "<b>Send the report?</b>\n"
            "Administrators will see it and the profile will be blocked for you. "
            "The user will not learn who reported."
        ),
        "report_send": "Send report",
        "report_comment_prompt": (
            "<b>Describe the reason</b>\n"
            "Write a comment of 1 to 300 characters.\n\n<i>/cancel — cancel.</i>"
        ),
        "report_saved": "<b>Report saved</b>\nThe profile is blocked for you.",
        "blocked_notice": (
            "<b>User blocked</b>\n"
            "Profiles are no longer visible to each other in the bot and the contact "
            "becomes unavailable.\n\n"
            "<i>You can block the user separately in the private Telegram chat.</i>"
        ),
    }
)

_RU_EXTRA.update(
    {
        "err_text_length": "Текст должен содержать {minimum}–{maximum} символов.",
        "err_no_contacts": "Не указывай контакты, @username и ссылки.",
        "err_age_invalid": "Возраст должен быть от 18 до 99 лет. Попробуй ещё раз 💜",
        "err_min_max": "Минимальный возраст не должен быть больше максимального.",
        "err_location_failed": "Не получилось определить геолокацию. Попробуй ещё раз.",
        "err_user_not_found": "Пользователь не найден.",
        "err_access_limited": "Доступ ограничен. Доступны /help, /privacy и /delete.",
        "err_create_or_show_profile": "Сначала создай анкету или снова сделай её видимой.",
        "err_add_username": "Добавь имя пользователя в настройках Telegram.",
        "err_profile_stale": "Данные анкеты устарели. Начни заново с /start.",
        "err_photo_and_consent": "Нужны фото и твоё согласие. Начни заново с /start.",
        "err_invalid_field": "Недопустимое поле или значение.",
        "err_create_profile_start": "Сначала создай анкету: /start",
        "err_profile_and_username": "Нужны анкета и имя пользователя Telegram.",
        "err_likes_limit": (
            "Лимит {limit} лайков исчерпан.\n"
            "Следующее обновление: {reset_at} UTC.\n\n"
            "💎 Premium снимает лимит лайков."
        ),
        "err_undo_limit": (
            "Возврат анкеты доступен {limit} раз в сутки.\n"
            "Следующее обновление: {reset_at} UTC.\n\n"
            "💎 Premium снимает лимит возвратов."
        ),
        "err_invalid_reaction": "Недопустимая реакция.",
        "err_profile_unavailable": (
            "Эта анкета сейчас недоступна или не соответствует твоим фильтрам."
        ),
        "err_match_unavailable": "Взаимная симпатия не найдена или недоступна тебе.",
        "err_match_unavailable_now": "Эта взаимная симпатия сейчас недоступна.",
        "err_invalid_page": "Недопустимая страница.",
        "err_invalid_profile": "Недопустимая анкета.",
        "err_profile_action_unavailable": "Действие с этой анкетой недоступно.",
        "err_report_comment": "Комментарий к жалобе слишком длинный или пустой.",
        "err_admin_only": "Этот раздел доступен только администратору.",
        "err_report_not_found": "Жалоба не найдена.",
        "err_invalid_action": "Недопустимое действие или жалоба.",
        "err_send_start": "Сначала отправь /start.",
        "err_invalid_premium_plan": "Недопустимый план Premium.",
        "err_premium_event": "Событие Premium уже обработано.",
        "err_photo_limit": "Достигнут лимит фото ({limit}).",
        "err_photo_limit_premium": (
            "Достигнут лимит фото ({limit}).\n\n"
            "💎 Premium позволяет добавить до {premium_limit} фото."
        ),
        "err_last_photo": "Нельзя удалить единственное фото. Сначала добавь другое.",
        "err_photo_not_found": "Фото не найдено.",
        "err_boost_premium": "Boost доступен только с Premium.",
        "err_boost_cooldown": (
            "Boost можно активировать снова через {hours} ч.\n"
            "Следующая активация: {next_at} UTC."
        ),
        "err_invalid_sort": "Недопустимая сортировка.",
        "err_incoming_premium": "Список входящих лайков доступен только с Premium.",
    }
)

_UZ.update(
    {
        "err_text_length": "Matn {minimum}–{maximum} belgidan iborat bo'lishi kerak.",
        "err_no_contacts": "Kontakt, @username va havolalarni ko'rsatmang.",
        "err_age_invalid": "Yosh 18–99 oralig'ida bo'lishi kerak. Qayta urinib ko'ring 💜",
        "err_min_max": "Minimal yosh maksimaldan katta bo'lmasligi kerak.",
        "err_location_failed": "Geolokatsiyani aniqlab bo'lmadi. Qayta urinib ko'ring.",
        "err_user_not_found": "Foydalanuvchi topilmadi.",
        "err_access_limited": "Kirish cheklangan. /help, /privacy va /delete mavjud.",
        "err_create_or_show_profile": "Avval profil yarating yoki uni yana ko'rinadigan qiling.",
        "err_add_username": "Telegram sozlamalarida foydalanuvchi nomini qo'shing.",
        "err_profile_stale": "Profil ma'lumotlari eskirgan. /start bilan qaytadan boshlang.",
        "err_photo_and_consent": "Foto va rozilik kerak. /start bilan qaytadan boshlang.",
        "err_invalid_field": "Maydon yoki qiymat yaroqsiz.",
        "err_create_profile_start": "Avval profil yarating: /start",
        "err_profile_and_username": "Profil va Telegram foydalanuvchi nomi kerak.",
        "err_likes_limit": (
            "Kunlik {limit} like limiti tugadi.\n"
            "Keyingi yangilanish: {reset_at} UTC.\n\n"
            "💎 Premium like limitini olib tashlaydi."
        ),
        "err_undo_limit": (
            "Profilni qaytarish kuniga {limit} marta mumkin.\n"
            "Keyingi yangilanish: {reset_at} UTC.\n\n"
            "💎 Premium qaytarish limitini olib tashlaydi."
        ),
        "err_invalid_reaction": "Reaksiya yaroqsiz.",
        "err_profile_unavailable": (
            "Bu profil hozir mavjud emas yoki filtrlaringizga mos kelmaydi."
        ),
        "err_match_unavailable": "O'zaro simpatiya topilmadi yoki siz uchun mavjud emas.",
        "err_match_unavailable_now": "Bu o'zaro simpatiya hozir mavjud emas.",
        "err_invalid_page": "Sahifa yaroqsiz.",
        "err_invalid_profile": "Profil yaroqsiz.",
        "err_profile_action_unavailable": "Bu profil bilan amal bajarib bo'lmaydi.",
        "err_report_comment": "Shikoyat izohi juda uzun yoki bo'sh.",
        "err_admin_only": "Bu bo'lim faqat administrator uchun.",
        "err_report_not_found": "Shikoyat topilmadi.",
        "err_invalid_action": "Amal yoki shikoyat yaroqsiz.",
        "err_send_start": "Avval /start yuboring.",
        "err_invalid_premium_plan": "Premium tarifi yaroqsiz.",
        "err_premium_event": "Premium hodisasi allaqachon qayta ishlangan.",
        "err_photo_limit": "Foto limiti tugadi ({limit}).",
        "err_photo_limit_premium": (
            "Foto limiti tugadi ({limit}).\n\n"
            "💎 Premium {premium_limit} tagacha foto qo'shishga imkon beradi."
        ),
        "err_last_photo": "Yagona fotoni o'chirib bo'lmaydi. Avval boshqasini qo'shing.",
        "err_photo_not_found": "Foto topilmadi.",
        "err_boost_premium": "Boost faqat Premium bilan mavjud.",
        "err_boost_cooldown": (
            "Boost ni {hours} soatdan so'ng qayta faollashtirish mumkin.\n"
            "Keyingi faollashtirish: {next_at} UTC."
        ),
        "err_invalid_sort": "Saralash yaroqsiz.",
        "err_incoming_premium": "Kiruvchi like'lar ro'yxati faqat Premium bilan mavjud.",
    }
)

_EN.update(
    {
        "err_text_length": "The text must be {minimum}–{maximum} characters long.",
        "err_no_contacts": "Do not include contacts, @username or links.",
        "err_age_invalid": "Age must be from 18 to 99. Try again 💜",
        "err_min_max": "The minimum age must not be greater than the maximum.",
        "err_location_failed": "Could not detect your location. Try again.",
        "err_user_not_found": "User not found.",
        "err_access_limited": "Access is restricted. /help, /privacy and /delete are available.",
        "err_create_or_show_profile": "Create a profile first or make it visible again.",
        "err_add_username": "Add a username in your Telegram settings.",
        "err_profile_stale": "Profile data is outdated. Start again with /start.",
        "err_photo_and_consent": "A photo and your consent are required. Start again with /start.",
        "err_invalid_field": "Invalid field or value.",
        "err_create_profile_start": "Create a profile first: /start",
        "err_profile_and_username": "A profile and a Telegram username are required.",
        "err_likes_limit": (
            "The daily limit of {limit} likes is used up.\n"
            "Next reset: {reset_at} UTC.\n\n"
            "💎 Premium removes the like limit."
        ),
        "err_undo_limit": (
            "You can return a profile {limit} time(s) per day.\n"
            "Next reset: {reset_at} UTC.\n\n"
            "💎 Premium removes the return limit."
        ),
        "err_invalid_reaction": "Invalid reaction.",
        "err_profile_unavailable": (
            "This profile is not available right now or does not match your filters."
        ),
        "err_match_unavailable": "The match was not found or is not available to you.",
        "err_match_unavailable_now": "This match is not available right now.",
        "err_invalid_page": "Invalid page.",
        "err_invalid_profile": "Invalid profile.",
        "err_profile_action_unavailable": "This action is not available for this profile.",
        "err_report_comment": "The report comment is too long or empty.",
        "err_admin_only": "This section is available to administrators only.",
        "err_report_not_found": "Report not found.",
        "err_invalid_action": "Invalid action or report.",
        "err_send_start": "Send /start first.",
        "err_invalid_premium_plan": "Invalid Premium plan.",
        "err_premium_event": "This Premium event was already processed.",
        "err_photo_limit": "Photo limit reached ({limit}).",
        "err_photo_limit_premium": (
            "Photo limit reached ({limit}).\n\n"
            "💎 Premium lets you add up to {premium_limit} photos."
        ),
        "err_last_photo": "You cannot delete your only photo. Add another one first.",
        "err_photo_not_found": "Photo not found.",
        "err_boost_premium": "Boost is available with Premium only.",
        "err_boost_cooldown": (
            "You can activate Boost again in {hours} h.\n"
            "Next activation: {next_at} UTC."
        ),
        "err_invalid_sort": "Invalid sorting.",
        "err_incoming_premium": "The incoming likes list is available with Premium only.",
    }
)

_RU_EXTRA.update(
    {
        "no_profiles": (
            "<b>Сейчас подходящих анкет нет 💜</b>\n"
            "Попробуй изменить настройки поиска или загляни позже."
        ),
        "no_likes": "<b>Пока нет новых лайков 💌</b>\nА пока можно посмотреть анкеты.",
        "trial_welcome": (
            "🎁 Вам доступен Premium бесплатно на {days} дней!\n\n"
            "Все Premium-возможности уже активированы.\n"
            "Действует до: {until}"
        ),
        "trial_reminder": (
            "⏳ Бесплатный Premium закончится завтра.\n"
            "Продлите Premium, чтобы сохранить доступ ко всем возможностям."
        ),
        "trial_expired": (
            "⌛ Бесплатный Premium закончился.\n"
            "Вы можете продолжить пользоваться ботом бесплатно или подключить Premium."
        ),
        "boost_activated": (
            "<b>🚀 Твоя анкета поднята!</b>\n\n"
            "Действует {minutes} минут. Твоя анкета будет показываться в приоритете "
            "среди подходящих кандидатов.\n\n"
            "Следующее поднятие доступно: {next_at}"
        ),
        "boost_active": (
            "<b>🚀 Поднятие уже активно</b>\n\n"
            "Осталось: {minutes} мин.\n"
            "Следующее поднятие доступно: {next_at}"
        ),
        "boost_cooldown": (
            "<b>🚀 Поднятие анкеты</b>\n\n"
            "Следующее поднятие доступно: {next_at}\n\n"
            "Поднятие дает приоритет в показе на 30 минут и доступно раз в 24 часа."
        ),
    }
)
_UZ.update(
    {
        "no_profiles": (
            "<b>Hozircha mos profil yo'q 💜</b>\n"
            "Qidiruv sozlamalarini o'zgartirib ko'ring yoki keyinroq qaytib keling."
        ),
        "no_likes": (
            "<b>Hozircha yangi like yo'q 💌</b>\n"
            "Ayni damda profillarni ko'rib chiqishingiz mumkin."
        ),
        "trial_welcome": (
            "🎁 Sizga {days} kunlik bepul Premium taqdim etiladi!\n\n"
            "Barcha Premium imkoniyatlari faollashtirilgan.\n"
            "Amal qiladi: {until}"
        ),
        "trial_reminder": (
            "⏳ Bepul Premium ertaga tugaydi.\n"
            "Barcha imkoniyatlarni saqlab qolish uchun Premium'ni uzaytiring."
        ),
        "trial_expired": (
            "⌛ Bepul Premium tugadi.\n"
            "Botdan bepul foydalanishni davom ettirishingiz yoki Premium ulashingiz mumkin."
        ),
        "boost_activated": (
            "<b>🚀 Profilingiz ko'tarildi!</b>\n\n"
            "{minutes} daqiqa amal qiladi. Profilingiz mos nomzodlar orasida birinchi "
            "navbatda ko'rsatiladi.\n\n"
            "Keyingi ko'tarish mumkin: {next_at}"
        ),
        "boost_active": (
            "<b>🚀 Ko'tarish allaqachon faol</b>\n\n"
            "Qoldi: {minutes} daq.\n"
            "Keyingi ko'tarish mumkin: {next_at}"
        ),
        "boost_cooldown": (
            "<b>🚀 Profilni ko'tarish</b>\n\n"
            "Keyingi ko'tarish mumkin: {next_at}\n\n"
            "Ko'tarish 30 daqiqa davomida ko'rsatishda ustunlik beradi va kuniga bir marta "
            "mavjud."
        ),
    }
)
_EN.update(
    {
        "no_profiles": (
            "<b>No suitable profiles right now 💜</b>\n"
            "Try changing your search settings or come back later."
        ),
        "no_likes": "<b>No new likes yet 💌</b>\nMeanwhile you can browse profiles.",
        "trial_welcome": (
            "🎁 You have free Premium for {days} days!\n\n"
            "All Premium features are already active.\n"
            "Valid until: {until}"
        ),
        "trial_reminder": (
            "⏳ Your free Premium ends tomorrow.\n"
            "Extend Premium to keep all the features."
        ),
        "trial_expired": (
            "⌛ Your free Premium has ended.\n"
            "You can keep using the bot for free or subscribe to Premium."
        ),
        "boost_activated": (
            "<b>🚀 Your profile is boosted!</b>\n\n"
            "Active for {minutes} minutes. Your profile is shown with priority among "
            "suitable candidates.\n\n"
            "Next boost available: {next_at}"
        ),
        "boost_active": (
            "<b>🚀 Boost is already active</b>\n\n"
            "Time left: {minutes} min.\n"
            "Next boost available: {next_at}"
        ),
        "boost_cooldown": (
            "<b>🚀 Profile boost</b>\n\n"
            "Next boost available: {next_at}\n\n"
            "A boost gives priority in the feed for 30 minutes and is available once "
            "every 24 hours."
        ),
    }
)

_RU_EXTRA.update(
    {
        "premium_intro": (
            "<b>💎 Premium — больше шансов на знакомство</b>\n"
            "<i>Сравни возможности и выбери то, что подходит тебе.</i>\n\n"
            "<b>Обычный аккаунт  →  Premium</b>\n\n"
            "💜 <b>Лайки в сутки</b>\n"
            "30  →  <b>без ограничений</b>\n\n"
            "↩️ <b>Возврат анкет</b>\n"
            "1 в сутки  →  <b>без ограничений</b>\n\n"
            "📸 <b>Фото в анкете</b>\n"
            "1 фото  →  <b>до 5 фото</b>\n\n"
            "📍 <b>Точный радиус поиска</b>\n"
            "обычный поиск  →  <b>10 / 25 / 50 / 100 км</b>\n\n"
            "💌 <b>Входящие лайки</b>\n"
            "по одному  →  <b>список и сортировка</b>\n\n"
            "🚀 <b>Boost анкеты</b>\n"
            "недоступен  →  <b>поднятие на 30 минут</b> раз в сутки\n\n"
            "Плюс заметный значок <b>💎 Premium</b> в анкете.\n\n"
            "<b>Выбери срок Premium:</b>"
        ),
    }
)
_UZ.update(
    {
        "premium_intro": (
            "<b>💎 Premium — tanishuv imkoniyati ko'proq</b>\n"
            "<i>Imkoniyatlarni solishtiring va o'zingizga mosini tanlang.</i>\n\n"
            "<b>Oddiy akkaunt  →  Premium</b>\n\n"
            "💜 <b>Kunlik like'lar</b>\n"
            "30  →  <b>cheklovsiz</b>\n\n"
            "↩️ <b>Profilni qaytarish</b>\n"
            "kuniga 1  →  <b>cheklovsiz</b>\n\n"
            "📸 <b>Profildagi foto</b>\n"
            "1 foto  →  <b>5 tagacha foto</b>\n\n"
            "📍 <b>Aniq qidiruv radiusi</b>\n"
            "oddiy qidiruv  →  <b>10 / 25 / 50 / 100 km</b>\n\n"
            "💌 <b>Kiruvchi like'lar</b>\n"
            "birma-bir  →  <b>ro'yxat va saralash</b>\n\n"
            "🚀 <b>Profil Boost</b>\n"
            "mavjud emas  →  kuniga bir marta <b>30 daqiqaga ko'tarish</b>\n\n"
            "Bundan tashqari profilda ko'zga tashlanadigan <b>💎 Premium</b> belgisi.\n\n"
            "<b>Premium muddatini tanlang:</b>"
        ),
    }
)
_EN.update(
    {
        "premium_intro": (
            "<b>💎 Premium — more chances to connect</b>\n"
            "<i>Compare the features and pick what suits you.</i>\n\n"
            "<b>Regular account  →  Premium</b>\n\n"
            "💜 <b>Likes per day</b>\n"
            "30  →  <b>no limits</b>\n\n"
            "↩️ <b>Return profiles</b>\n"
            "1 per day  →  <b>no limits</b>\n\n"
            "📸 <b>Profile photos</b>\n"
            "1 photo  →  <b>up to 5 photos</b>\n\n"
            "📍 <b>Precise search radius</b>\n"
            "regular search  →  <b>10 / 25 / 50 / 100 km</b>\n\n"
            "💌 <b>Incoming likes</b>\n"
            "one by one  →  <b>list and sorting</b>\n\n"
            "🚀 <b>Profile Boost</b>\n"
            "not available  →  <b>a 30-minute boost</b> once per day\n\n"
            "Plus a prominent <b>💎 Premium</b> badge on your profile.\n\n"
            "<b>Choose your Premium period:</b>"
        ),
    }
)

_RU_EXTRA.update(
    {
        "premium_active": (
            "<b>💎 У тебя Premium</b>\n"
            "<i>Все расширенные возможности уже доступны.</i>\n\n"
            "🗓 Действует до: <b>{until}</b>\n"
            "⏳ Осталось дней: <b>{days}</b>\n\n"
            "<b>Что включено:</b>\n"
            "∞ лайков и возвратов анкет\n"
            "📸 до 5 фотографий\n"
            "📍 радиус 10 / 25 / 50 / 100 км\n"
            "💌 список входящих лайков с сортировкой\n"
            "🚀 Boost анкеты на 30 минут\n"
            "💎 значок Premium в анкете\n\n"
            "<b>Продлить Premium:</b>"
        ),
        "premium_trial_active": (
            "<b>🎁 Пробный Premium активен до {until}</b>\n\n"
            "Все Premium-возможности уже активированы.\n\n"
            "Продлить доступ можно заранее — оплаченный срок начнётся после пробного периода."
        ),
        "premium_paid_active": (
            "<b>💜 Premium активен до {until}</b>\n\n"
            "Все Premium-возможности уже активированы.\n\n"
            "Новый оплаченный срок добавится к текущему остатку."
        ),
        "premium_not_connected": (
            "<b>Оплата ещё не подключена</b>\n\n"
            "Функции Premium полностью реализованы, но прием платежей через Telegram Stars "
            "будет подключен на следующем этапе.\n\n"
            "Администратор может выдать Premium для тестирования командой:\n"
            "<code>/premium_grant TELEGRAM_ID premium_1m</code>"
        ),
        "premium_plan_details": (
            "<b>💎 Premium на {plan}</b>\n\n"
            "Стоимость: <b>{price} ⭐️</b>\n"
            "Срок: <b>{plan}</b>\n"
            "Тип покупки: <b>разовая, без автосписания</b>\n\n"
            "Новый срок добавится к уже оплаченному остатку. Нажимая кнопку ниже, "
            "ты принимаешь /terms."
        ),
        "premium_settings_text": (
            "<b>⚙️ Настройки Premium</b>\n\n"
            "Значок 💎: {badge}\n\n"
            "Значок показывается в твоей анкете, если настройка включена."
        ),
        "premium_badge_shown": "показывается",
        "premium_badge_hidden": "скрыт",
        "premium_badge_show_button": "Показать значок 💎",
        "premium_badge_hide_button": "Скрыть значок 💎",
        "premium_badge_done": "<b>Готово!</b> Значок 💎 {badge} в твоей анкете.",
        "err_premium_only": "Эта функция доступна только для Premium пользователей.",
        "err_invalid_tariff": "Недействительный тариф.",
    }
)

_UZ.update(
    {
        "premium_active": (
            "<b>💎 Sizda Premium bor</b>\n"
            "<i>Barcha kengaytirilgan imkoniyatlar allaqachon mavjud.</i>\n\n"
            "🗓 Amal qiladi: <b>{until}</b>\n"
            "⏳ Qolgan kunlar: <b>{days}</b>\n\n"
            "<b>Nimalar kiradi:</b>\n"
            "∞ like va profilni qaytarish\n"
            "📸 5 tagacha foto\n"
            "📍 radius 10 / 25 / 50 / 100 km\n"
            "💌 kiruvchi like'lar ro'yxati saralash bilan\n"
            "🚀 30 daqiqalik profil Boost\n"
            "💎 profildagi Premium belgisi\n\n"
            "<b>Premium'ni uzaytirish:</b>"
        ),
        "premium_trial_active": (
            "<b>🎁 Sinov Premium {until} gacha faol</b>\n\n"
            "Barcha Premium imkoniyatlari faollashtirilgan.\n\n"
            "Muddatni oldindan uzaytirish mumkin — to'langan muddat sinov davridan keyin "
            "boshlanadi."
        ),
        "premium_paid_active": (
            "<b>💜 Premium {until} gacha faol</b>\n\n"
            "Barcha Premium imkoniyatlari faollashtirilgan.\n\n"
            "Yangi to'langan muddat joriy qoldiqqa qo'shiladi."
        ),
        "premium_not_connected": (
            "<b>To'lov hali ulanmagan</b>\n\n"
            "Premium funksiyalari to'liq tayyor, biroq Telegram Stars orqali to'lov qabul "
            "qilish keyingi bosqichda ulanadi.\n\n"
            "Administrator sinov uchun Premium'ni quyidagi buyruq bilan berishi mumkin:\n"
            "<code>/premium_grant TELEGRAM_ID premium_1m</code>"
        ),
        "premium_plan_details": (
            "<b>💎 {plan} Premium</b>\n\n"
            "Narxi: <b>{price} ⭐️</b>\n"
            "Muddat: <b>{plan}</b>\n"
            "Xarid turi: <b>bir martalik, avtomatik yechib olishsiz</b>\n\n"
            "Yangi muddat to'langan qoldiqqa qo'shiladi. Quyidagi tugmani bosib, siz /terms "
            "shartlarini qabul qilasiz."
        ),
        "premium_settings_text": (
            "<b>⚙️ Premium sozlamalari</b>\n\n"
            "💎 belgisi: {badge}\n\n"
            "Belgi sozlama yoqilgan bo'lsa profilingizda ko'rsatiladi."
        ),
        "premium_badge_shown": "ko'rsatiladi",
        "premium_badge_hidden": "yashirilgan",
        "premium_badge_show_button": "💎 belgisini ko'rsatish",
        "premium_badge_hide_button": "💎 belgisini yashirish",
        "premium_badge_done": "<b>Tayyor!</b> 💎 belgisi profilingizda {badge}.",
        "err_premium_only": "Bu funksiya faqat Premium foydalanuvchilar uchun.",
        "err_invalid_tariff": "Tarif yaroqsiz.",
    }
)
_EN.update(
    {
        "premium_active": (
            "<b>💎 You have Premium</b>\n"
            "<i>All extended features are already available.</i>\n\n"
            "🗓 Valid until: <b>{until}</b>\n"
            "⏳ Days left: <b>{days}</b>\n\n"
            "<b>What is included:</b>\n"
            "∞ likes and profile returns\n"
            "📸 up to 5 photos\n"
            "📍 radius 10 / 25 / 50 / 100 km\n"
            "💌 sorted incoming likes list\n"
            "🚀 a 30-minute profile Boost\n"
            "💎 Premium badge on your profile\n\n"
            "<b>Extend Premium:</b>"
        ),
        "premium_trial_active": (
            "<b>🎁 Trial Premium is active until {until}</b>\n\n"
            "All Premium features are already active.\n\n"
            "You can extend in advance — the paid period starts after the trial ends."
        ),
        "premium_paid_active": (
            "<b>💜 Premium is active until {until}</b>\n\n"
            "All Premium features are already active.\n\n"
            "A new paid period is added to the current remaining time."
        ),
        "premium_not_connected": (
            "<b>Payments are not connected yet</b>\n\n"
            "Premium features are fully implemented, but accepting payments via Telegram Stars "
            "will be connected at the next stage.\n\n"
            "An administrator can grant Premium for testing with:\n"
            "<code>/premium_grant TELEGRAM_ID premium_1m</code>"
        ),
        "premium_plan_details": (
            "<b>💎 Premium for {plan}</b>\n\n"
            "Price: <b>{price} ⭐️</b>\n"
            "Period: <b>{plan}</b>\n"
            "Purchase type: <b>one-time, no auto-renewal</b>\n\n"
            "A new period is added to your paid balance. By tapping the button below you "
            "accept /terms."
        ),
        "premium_settings_text": (
            "<b>⚙️ Premium settings</b>\n\n"
            "Badge 💎: {badge}\n\n"
            "The badge is shown on your profile when this setting is on."
        ),
        "premium_badge_shown": "shown",
        "premium_badge_hidden": "hidden",
        "premium_badge_show_button": "Show 💎 badge",
        "premium_badge_hide_button": "Hide 💎 badge",
        "premium_badge_done": "<b>Done!</b> The 💎 badge is {badge} on your profile.",
        "err_premium_only": "This feature is available to Premium users only.",
        "err_invalid_tariff": "Invalid plan.",
    }
)

_RU_EXTRA.update(
    {
        "err_sales_paused": "Новые покупки Premium временно приостановлены.",
        "err_purchase_unavailable": "Покупка Premium сейчас недоступна.",
        "err_order_not_found_owner": "Заказ не найден или принадлежит другому пользователю.",
        "err_order_closed": "Этот заказ уже закрыт. Выбери тариф заново.",
        "err_order_expired": "Время ожидания заказа истекло. Выбери тариф заново.",
        "err_unknown_order": "Неизвестный заказ. Создай новый счёт в разделе Premium.",
        "err_order_no_invoice": "Заказ не найден. Создай новый счёт в разделе Premium.",
        "err_invoice_other_user": "Этот счёт создан для другого пользователя.",
        "err_invoice_amount": "Сумма счёта не совпала с заказом. Оплата остановлена.",
        "err_invoice_not_ready": "Заказ уже закрыт или ещё не готов к оплате.",
        "err_confirm_terms_first": "Сначала подтверди условия покупки в боте.",
        "err_invoice_expired": "Время ожидания счёта истекло. Создай новый заказ.",
        "err_checkout_failed": "Не удалось проверить заказ. Попробуй создать новый счёт.",
        "err_order_not_found": "Заказ не найден.",
        "err_no_refundable_payment": "Для этого заказа нет платежа, доступного к возврату.",
        "err_invalid_payment_button": "Недействительная кнопка платежа.",
        "err_no_refund": "Этот платёж нельзя вернуть.",
        "err_invalid_payment_action": "Недействительное действие с платежом.",
        "refund_unknown": (
            "Результат возврата неизвестен. Не повторяй его вслепую: запусти /stars_reconcile."
        ),
        "err_refund_not_confirmed": "Telegram не подтвердил возврат. Выполни сверку.",
    }
)
_UZ.update(
    {
        "err_sales_paused": "Premium uchun yangi xaridlar vaqtincha to'xtatilgan.",
        "err_purchase_unavailable": "Premium xaridi hozir mavjud emas.",
        "err_order_not_found_owner": "Buyurtma topilmadi yoki boshqa foydalanuvchiga tegishli.",
        "err_order_closed": "Bu buyurtma allaqachon yopilgan. Tarifni qaytadan tanlang.",
        "err_order_expired": "Buyurtma kutish muddati tugadi. Tarifni qaytadan tanlang.",
        "err_unknown_order": "Noma'lum buyurtma. Premium bo'limida yangi hisob yarating.",
        "err_order_no_invoice": "Buyurtma topilmadi. Premium bo'limida yangi hisob yarating.",
        "err_invoice_other_user": "Bu hisob boshqa foydalanuvchi uchun yaratilgan.",
        "err_invoice_amount": "Hisob summasi buyurtmaga mos kelmadi. To'lov to'xtatildi.",
        "err_invoice_not_ready": "Buyurtma yopilgan yoki hali to'lovga tayyor emas.",
        "err_confirm_terms_first": "Avval botda xarid shartlarini tasdiqlang.",
        "err_invoice_expired": "Hisob kutish muddati tugadi. Yangi buyurtma yarating.",
        "err_checkout_failed": "Buyurtmani tekshirib bo'lmadi. Yangi hisob yaratib ko'ring.",
        "err_order_not_found": "Buyurtma topilmadi.",
        "err_no_refundable_payment": "Bu buyurtma uchun qaytarish mumkin bo'lgan to'lov yo'q.",
        "err_invalid_payment_button": "To'lov tugmasi yaroqsiz.",
        "err_no_refund": "Bu to'lovni qaytarib bo'lmaydi.",
        "err_invalid_payment_action": "To'lov bilan amal yaroqsiz.",
        "refund_unknown": (
            "Qaytarish natijasi noma'lum. Uni ko'r-ko'rona takrorlamang: /stars_reconcile "
            "ni ishga tushiring."
        ),
        "err_refund_not_confirmed": "Telegram qaytarishni tasdiqlamadi. Solishtirishni bajaring.",
    }
)
_EN.update(
    {
        "err_sales_paused": "New Premium purchases are temporarily paused.",
        "err_purchase_unavailable": "Premium purchase is not available right now.",
        "err_order_not_found_owner": "Order not found or it belongs to another user.",
        "err_order_closed": "This order is already closed. Choose a plan again.",
        "err_order_expired": "The order waiting time has expired. Choose a plan again.",
        "err_unknown_order": "Unknown order. Create a new invoice in the Premium section.",
        "err_order_no_invoice": "Order not found. Create a new invoice in the Premium section.",
        "err_invoice_other_user": "This invoice was created for another user.",
        "err_invoice_amount": "The invoice amount did not match the order. Payment stopped.",
        "err_invoice_not_ready": "The order is closed or not ready for payment yet.",
        "err_confirm_terms_first": "Confirm the purchase terms in the bot first.",
        "err_invoice_expired": "The invoice waiting time has expired. Create a new order.",
        "err_checkout_failed": "Could not verify the order. Try creating a new invoice.",
        "err_order_not_found": "Order not found.",
        "err_no_refundable_payment": "This order has no payment available for a refund.",
        "err_invalid_payment_button": "Invalid payment button.",
        "err_no_refund": "This payment cannot be refunded.",
        "err_invalid_payment_action": "Invalid payment action.",
        "refund_unknown": (
            "The refund result is unknown. Do not repeat it blindly: run /stars_reconcile."
        ),
        "err_refund_not_confirmed": "Telegram did not confirm the refund. Run reconciliation.",
    }
)

_RU_EXTRA.update(
    {
        "payment_success": (
            "<b>✅ Оплата получена — Premium активирован</b>\n\n"
            "Заказ: <code>{order}</code>\n"
            "Доступ действует до: <b>{until}</b>\n\n"
            "Спасибо! Управлять Premium можно через кнопку 💎 Premium."
        ),
        "invoice_already_sent": "Счёт уже отправлен выше. Открой его и нажми кнопку оплаты.",
        "invoice_sending": "Счёт уже создаётся. Подожди несколько секунд.",
        "invoice_title": "Premium «Рядом»: {plan}",
        "invoice_description": (
            "Разовая покупка Premium на {plan}. Без автосписания и автопродления."
        ),
        "invoice_label": "Premium на {plan}",
        "invoice_error": (
            "Не удалось отправить счёт. Покупка не состоялась, Stars не списаны. "
            "Попробуй нажать кнопку оплаты ещё раз."
        ),
        "payment_review": (
            "Платёж получен, но параметры требуют проверки. Premium не начислен автоматически. "
            "Отправь /paysupport — администратор увидит платёж."
        ),
        "refund_ack": (
            "<b>Возврат Stars учтён</b>\n\n"
            "Доступ по возвращённой покупке скорректирован. Другие покупки и "
            "административные выдачи сохранены."
        ),
        "paysupport_admin": (
            "<b>💳 Обращение по оплате</b>\n"
            "Пользователь: <code>{telegram_id}</code>\n"
            "Заказ: <code>{order}</code>\n"
            "Статус: {status}"
        ),
        "paysupport_none": "не найден",
        "paysupport_no_order": "нет заказа",
        "paysupport_sent": (
            "Обращение по заказу <code>{order}</code> передано администраторам. "
            "Они проверят оплату и при необходимости выполнят возврат Stars."
        ),
        "paysupport_failed": (
            "Не удалось доставить обращение администраторам. Попробуй позже. "
            "Сохрани номер заказа: <code>{order}</code>."
        ),
        "refund_button": "Вернуть Stars",
        "payadmin_title": "<b>💳 Заказы Premium</b>\nСтраница {page}",
        "payadmin_order": (
            "<b>💳 Заказ Premium</b>\n"
            "Номер: <code>{order}</code>\n"
            "Пользователь: <code>{buyer}</code>\n"
            "Тариф: {plan}\n"
            "Сумма: {price} {currency}\n"
            "Статус заказа: {status}\n"
            "Статус платежа: {payment_status}"
        ),
        "payadmin_no_payment": "нет",
        "payadmin_back": "💳 К заказам",
        "refund_confirm_prompt": (
            "<b>Подтверди возврат</b>\n"
            "Пользователь: <code>{buyer}</code>\n"
            "Сумма: <b>{price} ⭐️</b>\n"
            "Заказ: <code>{order}</code>"
        ),
        "refund_yes": "Да, вернуть Stars",
        "refund_done": "<b>Возврат выполнен</b>\nStars возвращены, доступ скорректирован.",
        "reconcile_done": (
            "<b>Сверка Stars завершена</b>\n"
            "Входящие счета: {incoming}\n"
            "Возвраты: {refunded}\n"
            "Прочие операции: {skipped}"
        ),
    }
)
_UZ.update(
    {
        "payment_success": (
            "<b>✅ To'lov qabul qilindi — Premium faollashtirildi</b>\n\n"
            "Buyurtma: <code>{order}</code>\n"
            "Kirish muddati: <b>{until}</b>\n\n"
            "Rahmat! Premium'ni 💎 Premium tugmasi orqali boshqarishingiz mumkin."
        ),
        "invoice_already_sent": (
            "Hisob yuqorida allaqachon yuborilgan. Uni ochib, to'lov tugmasini bosing."
        ),
        "invoice_sending": "Hisob yaratilmoqda. Bir necha soniya kuting.",
        "invoice_title": "«Рядом» Premium: {plan}",
        "invoice_description": (
            "Premium uchun bir martalik xarid: {plan}. Avtomatik yechib olish va avtomatik "
            "yangilash yo'q."
        ),
        "invoice_label": "{plan} uchun Premium",
        "invoice_error": (
            "Hisobni yuborib bo'lmadi. Xarid amalga oshmadi, Stars yechilmadi. "
            "To'lov tugmasini yana bosib ko'ring."
        ),
        "payment_review": (
            "To'lov qabul qilindi, ammo parametrlarni tekshirish kerak. Premium avtomatik "
            "berilmadi. /paysupport yuboring — administrator to'lovni ko'radi."
        ),
        "refund_ack": (
            "<b>Stars qaytarilishi hisobga olindi</b>\n\n"
            "Qaytarilgan xarid bo'yicha kirish tuzatildi. Boshqa xaridlar va administrator "
            "bergan imtiyozlar saqlandi."
        ),
        "paysupport_admin": (
            "<b>💳 To'lov bo'yicha murojaat</b>\n"
            "Foydalanuvchi: <code>{telegram_id}</code>\n"
            "Buyurtma: <code>{order}</code>\n"
            "Holat: {status}"
        ),
        "paysupport_none": "topilmadi",
        "paysupport_no_order": "buyurtma yo'q",
        "paysupport_sent": (
            "<code>{order}</code> buyurtmasi bo'yicha murojaat administratorlarga yuborildi. "
            "Ular to'lovni tekshiradi va zarur bo'lsa Stars qaytaradi."
        ),
        "paysupport_failed": (
            "Murojaatni administratorlarga yuborib bo'lmadi. Keyinroq urinib ko'ring. "
            "Buyurtma raqamini saqlab qo'ying: <code>{order}</code>."
        ),
        "refund_button": "Stars ni qaytarish",
        "payadmin_title": "<b>💳 Premium buyurtmalari</b>\nSahifa {page}",
        "payadmin_order": (
            "<b>💳 Premium buyurtmasi</b>\n"
            "Raqam: <code>{order}</code>\n"
            "Foydalanuvchi: <code>{buyer}</code>\n"
            "Tarif: {plan}\n"
            "Summa: {price} {currency}\n"
            "Buyurtma holati: {status}\n"
            "To'lov holati: {payment_status}"
        ),
        "payadmin_no_payment": "yo'q",
        "payadmin_back": "💳 Buyurtmalarga",
        "refund_confirm_prompt": (
            "<b>Qaytarishni tasdiqlang</b>\n"
            "Foydalanuvchi: <code>{buyer}</code>\n"
            "Summa: <b>{price} ⭐️</b>\n"
            "Buyurtma: <code>{order}</code>"
        ),
        "refund_yes": "Ha, Stars ni qaytarish",
        "refund_done": "<b>Qaytarish bajarildi</b>\nStars qaytarildi, kirish tuzatildi.",
        "reconcile_done": (
            "<b>Stars solishtirish tugadi</b>\n"
            "Kiruvchi hisoblar: {incoming}\n"
            "Qaytarishlar: {refunded}\n"
            "Boshqa amallar: {skipped}"
        ),
    }
)
_EN.update(
    {
        "payment_success": (
            "<b>✅ Payment received — Premium activated</b>\n\n"
            "Order: <code>{order}</code>\n"
            "Access valid until: <b>{until}</b>\n\n"
            "Thank you! Manage Premium with the 💎 Premium button."
        ),
        "invoice_already_sent": "The invoice has already been sent above. Open it and tap pay.",
        "invoice_sending": "The invoice is being created. Wait a few seconds.",
        "invoice_title": "Рядом Premium: {plan}",
        "invoice_description": (
            "One-time Premium purchase for {plan}. No auto-charge and no auto-renewal."
        ),
        "invoice_label": "Premium for {plan}",
        "invoice_error": (
            "Could not send the invoice. The purchase did not happen and no Stars were "
            "charged. Try tapping the pay button again."
        ),
        "payment_review": (
            "The payment was received, but the parameters need checking. Premium was not "
            "granted automatically. Send /paysupport — an administrator will see the payment."
        ),
        "refund_ack": (
            "<b>Stars refund recorded</b>\n\n"
            "Access for the refunded purchase was adjusted. Other purchases and admin grants "
            "are kept."
        ),
        "paysupport_admin": (
            "<b>💳 Payment support request</b>\n"
            "User: <code>{telegram_id}</code>\n"
            "Order: <code>{order}</code>\n"
            "Status: {status}"
        ),
        "paysupport_none": "not found",
        "paysupport_no_order": "no order",
        "paysupport_sent": (
            "The request for order <code>{order}</code> was forwarded to administrators. "
            "They will check the payment and refund Stars if needed."
        ),
        "paysupport_failed": (
            "Could not deliver the request to administrators. Try later. "
            "Save your order number: <code>{order}</code>."
        ),
        "refund_button": "Refund Stars",
        "payadmin_title": "<b>💳 Premium orders</b>\nPage {page}",
        "payadmin_order": (
            "<b>💳 Premium order</b>\n"
            "Number: <code>{order}</code>\n"
            "User: <code>{buyer}</code>\n"
            "Plan: {plan}\n"
            "Amount: {price} {currency}\n"
            "Order status: {status}\n"
            "Payment status: {payment_status}"
        ),
        "payadmin_no_payment": "none",
        "payadmin_back": "💳 To orders",
        "refund_confirm_prompt": (
            "<b>Confirm the refund</b>\n"
            "User: <code>{buyer}</code>\n"
            "Amount: <b>{price} ⭐️</b>\n"
            "Order: <code>{order}</code>"
        ),
        "refund_yes": "Yes, refund Stars",
        "refund_done": "<b>Refund completed</b>\nStars refunded, access adjusted.",
        "reconcile_done": (
            "<b>Stars reconciliation finished</b>\n"
            "Incoming invoices: {incoming}\n"
            "Refunds: {refunded}\n"
            "Other operations: {skipped}"
        ),
    }
)

_RU_EXTRA.update(
    {
        "err_no_sender": "Не удалось определить отправителя команды.",
        "admin_panel": (
            "<b>🛡 Панель администратора</b>\n"
            "Пользователи: {users}\n"
            "Активные анкеты: {profiles}\n"
            "Взаимные симпатии: {matches}\n"
            "Открытые жалобы: {reports}\n\n"
            "/ban Telegram_ID — заблокировать\n"
            "/unban Telegram_ID — снять блокировку"
        ),
        "admin_reports_button": "⚠️ Жалобы",
        "err_ban_usage": "Укажи Telegram ID после команды: /ban 123456789",
        "admin_banned": "Пользователь заблокирован.",
        "admin_unbanned": "Блокировка снята. Анкета не активируется автоматически.",
        "err_grant_usage": "Формат: /premium_grant TELEGRAM_ID PLAN_CODE",
        "err_grant_plan_usage": (
            "Формат: /premium_grant TELEGRAM_ID PLAN_CODE\n"
            "План: premium_3d, premium_1m, premium_3m"
        ),
        "err_plan_invalid": "План должен быть: premium_3d, premium_1m или premium_3m",
        "admin_granted": (
            "<b>Premium выдан</b>\n"
            "Пользователь: <code>{telegram_id}</code>\n"
            "План: {plan}\n"
            "Действует до: {until}"
        ),
        "err_status_usage": "Формат: /premium_status TELEGRAM_ID",
        "admin_status": (
            "<b>Premium статус</b>\n"
            "Пользователь: <code>{telegram_id}</code>\n"
            "Статус: {status}{details}"
        ),
        "admin_status_active": "Активен",
        "admin_status_none": "Нет Premium",
        "admin_status_until": "\nДействует до: {until}\nОсталось дней: {days}",
        "err_revoke_usage": "Формат: /premium_revoke TELEGRAM_ID",
        "admin_revoked": "<b>Premium отозван</b>\nПользователь: <code>{telegram_id}</code>",
        "err_admin_button": "Недействительная кнопка администратора.",
        "err_admin_message": "Сообщение администратора недоступно.",
        "admin_report_row": "Жалоба #{report_id}",
        "admin_reports_page": "<b>⚠️ Открытые жалобы</b>\nСтраница {page}",
        "admin_no_reports": "<b>Открытых жалоб нет</b>",
        "admin_block_button": "Заблокировать",
        "admin_unblock_button": "Снять блокировку",
        "admin_reviewed_button": "Рассмотрено",
        "admin_report_detail": (
            "<b>Жалоба #{report_id}</b>\nПричина: {reason}\nСтатус: {status}"
        ),
        "admin_report_open": "открыта",
        "admin_report_closed": "рассмотрена",
        "admin_profile_deleted": "Текущая анкета удалена, но запись модерации сохранена.",
        "admin_action_done": (
            "<b>Действие выполнено</b>\n"
            "Снятие блокировки не активирует анкету автоматически."
        ),
        "err_admin_action": "Недопустимое действие администратора.",
    }
)
_UZ.update(
    {
        "err_no_sender": "Buyruq yuboruvchisini aniqlab bo'lmadi.",
        "admin_panel": (
            "<b>🛡 Administrator paneli</b>\n"
            "Foydalanuvchilar: {users}\n"
            "Faol profillar: {profiles}\n"
            "O'zaro simpatiyalar: {matches}\n"
            "Ochiq shikoyatlar: {reports}\n\n"
            "/ban Telegram_ID — bloklash\n"
            "/unban Telegram_ID — blokdan chiqarish"
        ),
        "admin_reports_button": "⚠️ Shikoyatlar",
        "err_ban_usage": "Buyruqdan keyin Telegram ID ko'rsating: /ban 123456789",
        "admin_banned": "Foydalanuvchi bloklandi.",
        "admin_unbanned": "Blokdan chiqarildi. Profil avtomatik faollashmaydi.",
        "err_grant_usage": "Format: /premium_grant TELEGRAM_ID PLAN_CODE",
        "err_grant_plan_usage": (
            "Format: /premium_grant TELEGRAM_ID PLAN_CODE\n"
            "Tarif: premium_3d, premium_1m, premium_3m"
        ),
        "err_plan_invalid": (
            "Tarif quyidagilardan biri bo'lishi kerak: premium_3d, premium_1m yoki premium_3m"
        ),
        "admin_granted": (
            "<b>Premium berildi</b>\n"
            "Foydalanuvchi: <code>{telegram_id}</code>\n"
            "Tarif: {plan}\n"
            "Amal qiladi: {until}"
        ),
        "err_status_usage": "Format: /premium_status TELEGRAM_ID",
        "admin_status": (
            "<b>Premium holati</b>\n"
            "Foydalanuvchi: <code>{telegram_id}</code>\n"
            "Holat: {status}{details}"
        ),
        "admin_status_active": "Faol",
        "admin_status_none": "Premium yo'q",
        "admin_status_until": "\nAmal qiladi: {until}\nQolgan kunlar: {days}",
        "err_revoke_usage": "Format: /premium_revoke TELEGRAM_ID",
        "admin_revoked": "<b>Premium bekor qilindi</b>\nFoydalanuvchi: <code>{telegram_id}</code>",
        "err_admin_button": "Administrator tugmasi yaroqsiz.",
        "err_admin_message": "Administrator xabari mavjud emas.",
        "admin_report_row": "Shikoyat #{report_id}",
        "admin_reports_page": "<b>⚠️ Ochiq shikoyatlar</b>\nSahifa {page}",
        "admin_no_reports": "<b>Ochiq shikoyatlar yo'q</b>",
        "admin_block_button": "Bloklash",
        "admin_unblock_button": "Blokdan chiqarish",
        "admin_reviewed_button": "Ko'rib chiqildi",
        "admin_report_detail": "<b>Shikoyat #{report_id}</b>\nSabab: {reason}\nHolat: {status}",
        "admin_report_open": "ochiq",
        "admin_report_closed": "ko'rib chiqilgan",
        "admin_profile_deleted": "Joriy profil o'chirilgan, ammo moderatsiya yozuvi saqlangan.",
        "admin_action_done": (
            "<b>Amal bajarildi</b>\nBlokdan chiqarish profilni avtomatik faollashtirmaydi."
        ),
        "err_admin_action": "Administrator amali yaroqsiz.",
    }
)
_EN.update(
    {
        "err_no_sender": "Could not determine the command sender.",
        "admin_panel": (
            "<b>🛡 Admin panel</b>\n"
            "Users: {users}\n"
            "Active profiles: {profiles}\n"
            "Matches: {matches}\n"
            "Open reports: {reports}\n\n"
            "/ban Telegram_ID — block\n"
            "/unban Telegram_ID — unblock"
        ),
        "admin_reports_button": "⚠️ Reports",
        "err_ban_usage": "Provide a Telegram ID after the command: /ban 123456789",
        "admin_banned": "User blocked.",
        "admin_unbanned": "Block removed. The profile is not activated automatically.",
        "err_grant_usage": "Format: /premium_grant TELEGRAM_ID PLAN_CODE",
        "err_grant_plan_usage": (
            "Format: /premium_grant TELEGRAM_ID PLAN_CODE\n"
            "Plan: premium_3d, premium_1m, premium_3m"
        ),
        "err_plan_invalid": "The plan must be: premium_3d, premium_1m or premium_3m",
        "admin_granted": (
            "<b>Premium granted</b>\n"
            "User: <code>{telegram_id}</code>\n"
            "Plan: {plan}\n"
            "Valid until: {until}"
        ),
        "err_status_usage": "Format: /premium_status TELEGRAM_ID",
        "admin_status": (
            "<b>Premium status</b>\n"
            "User: <code>{telegram_id}</code>\n"
            "Status: {status}{details}"
        ),
        "admin_status_active": "Active",
        "admin_status_none": "No Premium",
        "admin_status_until": "\nValid until: {until}\nDays left: {days}",
        "err_revoke_usage": "Format: /premium_revoke TELEGRAM_ID",
        "admin_revoked": "<b>Premium revoked</b>\nUser: <code>{telegram_id}</code>",
        "err_admin_button": "Invalid admin button.",
        "err_admin_message": "Admin message is unavailable.",
        "admin_report_row": "Report #{report_id}",
        "admin_reports_page": "<b>⚠️ Open reports</b>\nPage {page}",
        "admin_no_reports": "<b>No open reports</b>",
        "admin_block_button": "Block",
        "admin_unblock_button": "Unblock",
        "admin_reviewed_button": "Reviewed",
        "admin_report_detail": "<b>Report #{report_id}</b>\nReason: {reason}\nStatus: {status}",
        "admin_report_open": "open",
        "admin_report_closed": "reviewed",
        "admin_profile_deleted": (
            "The current profile was deleted, but the moderation record is kept."
        ),
        "admin_action_done": (
            "<b>Action completed</b>\nUnblocking does not activate the profile automatically."
        ),
        "err_admin_action": "Invalid administrator action.",
    }
)

_RU_EXTRA.update(
    {
        "err_language_invalid": "Не удалось выбрать язык. Попробуй ещё раз.",
    }
)
_UZ.update(
    {
        "err_language_invalid": "Tilni tanlashda xatolik yuz berdi. Qayta urinib ko'ring.",
    }
)
_EN.update(
    {
        "err_language_invalid": "Could not select the language. Try again.",
    }
)

_RU_EXTRA.update(
    {
        "err_album_not_allowed": "Отправь только одно фото, без альбома.",
    }
)
_UZ.update(
    {
        "err_album_not_allowed": "Faqat bitta foto yuboring, albomsiz.",
    }
)
_EN.update(
    {
        "err_album_not_allowed": "Send just one photo, without an album.",
    }
)

# --- Lexicon extensions (inserted before TRANSLATIONS) ---

_RU_EXTRA.update(
    {
        "err_choose_gender": "Выбери пол с помощью кнопок выше.",
        "err_choose_button": "Выбери вариант с помощью кнопок выше.",
        "payment_terms": (
            "<b>📄 Условия покупки Premium</b>\n\n"
            "Premium — платный доступ внутри бота «Рядом» и не является подпиской Telegram "
            "Premium. Покупка разовая: автоматического списания и автопродления нет.\n\n"
            "Срок тарифа добавляется к более поздней дате: текущему времени, окончанию trial "
            "или действующему оплаченному Premium. Тариф на 3 дня действует 72 часа; месячные "
            "тарифы считаются календарными месяцами с переносом на последний существующий день "
            "месяца.\n\n"
            "Оплата производится Telegram Stars. Premium выдаётся только после сообщения "
            "Telegram об успешной оплате. Отмена счёта не меняет текущий доступ.\n\n"
            "Для вопроса по платежу или запроса возврата отправь /paysupport. Укажи номер "
            "заказа, если он известен. Возврат рассматривается администратором и выполняется "
            "через Telegram."
        ),
        "cmd_start": "Меню и регистрация",
        "cmd_help": "Помощь",
        "cmd_privacy": "Конфиденциальность",
        "cmd_terms": "Условия покупки Premium",
        "cmd_paysupport": "Поддержка по платежам",
        "cmd_cancel": "Отменить действие",
        "cmd_id": "Мой Telegram ID",
        "cmd_delete": "Удалить анкету",
    }
)
_UZ.update(
    {
        "err_choose_gender": "Yuqoridagi tugmalar orqali jinsni tanlang.",
        "err_choose_button": "Yuqoridagi tugmalar orqali variantni tanlang.",
        "payment_terms": (
            "<b>📄 Premium xarid shartlari</b>\n\n"
            "Premium — «Рядом» boti ichidagi pullik kirish huquqi va Telegram Premium "
            "obunasi emas. Xarid bir martalik: avtomatik yechib olish va avtomatik uzaytirish "
            "yo'q.\n\n"
            "Tarif muddati keyingi sanaga qo'shiladi: joriy vaqt, trial tugashi yoki amaldagi "
            "pullik Premium. 3 kunlik tarif 72 soat davom etadi; oylik tariflar kalendar oyida "
            "hisoblanadi va mavjud oyning oxirgi kuniga o'tadi.\n\n"
            "To'lov Telegram Stars orqali amalga oshiriladi. Premium faqat Telegram "
            "muvaffaqiyatli to'lov haqida xabar bergandan keyin beriladi. Hisobni bekor qilish "
            "joriy kirishga ta'sir qilmaydi.\n\n"
            "To'lov bo'yicha savol yoki pulni qaytarish so'rovi uchun /paysupport yuboring. "
            "Agar ma'lum bo'lsa, buyurtma raqamini ko'rsating. Qaytarish administrator "
            "tomonidan ko'rib chiqiladi va Telegram orqali bajariladi."
        ),
        "cmd_start": "Menyu va ro'yxatdan o'tish",
        "cmd_help": "Yordam",
        "cmd_privacy": "Maxfiylik",
        "cmd_terms": "Premium xarid shartlari",
        "cmd_paysupport": "To'lov bo'yicha yordam",
        "cmd_cancel": "Amalni bekor qilish",
        "cmd_id": "Mening Telegram ID",
        "cmd_delete": "Profilni o'chirish",
    }
)
_EN.update(
    {
        "err_choose_gender": "Choose your gender with the buttons above.",
        "err_choose_button": "Choose an option with the buttons above.",
        "payment_terms": (
            "<b>📄 Premium purchase terms</b>\n\n"
            "Premium is paid access inside the «Рядом» bot and is not a Telegram Premium "
            "subscription. The purchase is one-time: there is no automatic charge or "
            "auto-renewal.\n\n"
            "The plan term is added to the later date: the current time, the end of the trial, "
            "or the currently active paid Premium. The 3-day plan lasts 72 hours; monthly plans "
            "are counted as calendar months and roll over to the last existing day of the "
            "month.\n\n"
            "Payment is made with Telegram Stars. Premium is granted only after Telegram "
            "reports a successful payment. Cancelling the invoice does not change the current "
            "access.\n\n"
            "For a payment question or a refund request, send /paysupport. Include the order "
            "number if you know it. A refund is reviewed by an administrator and processed "
            "through Telegram."
        ),
        "cmd_start": "Menu and sign-up",
        "cmd_help": "Help",
        "cmd_privacy": "Privacy",
        "cmd_terms": "Premium purchase terms",
        "cmd_paysupport": "Payment support",
        "cmd_cancel": "Cancel the action",
        "cmd_id": "My Telegram ID",
        "cmd_delete": "Delete profile",
    }
)

# Telegram clients report Kyrgyz as "ky"; the bot uses the shorter "kg" code.
_LANGUAGE_ALIASES: Final = {"ky": "kg"}

_KG: Final = {
    "menu_discover": "💜 Анкеталарды көрүү",
    "menu_profile": "👤 Менин анкетам",
    "menu_likes": "💌 Лайктар",
    "menu_matches": "✨ Озара жактыруулар",
    "menu_settings": "⚙️ Жөндөөлөр",
    "menu_premium": "💎 Premium",
    "menu_help": "❔ Жардам",
    "menu_placeholder": "Аракетти тандаңыз 💜",
    "home": (
        "<b>💜 Бул жерде экениңиз жакшы!</b>\n"
        "Анкеталарды көрүңүз же озара жактырууларыңызга кириңиз."
    ),
    "profile_missing": "Анкета табылган жок. Аны /start аркылуу түзүңүз.",
    "profile_photo_error": "Мурунку сүрөттү ачуу мүмкүн болбоду. «Сүрөт» басып, жаңысын жүктөңүз.",  # noqa: E501
    "profile_status_active": "<b>Анкета статусу:</b> активдүү",
    "profile_status_hidden": "<b>Анкета статусу:</b> жашырылган",
    "location_set": "көрсөтүлгөн",
    "location_unset": "көрсөтүлгөн эмес",
    "search_settings": (
        "<b>⚙️ Издөө жөндөөлөрү</b>\nЖаш: {min_age}–{max_age}\nГеолокация: {location}"
    ),
    "age_search": "Издөө үчүн жаш",
    "change_location": "📍 Геолокацияны өзгөртүү",
    "seeking_label": "Кимди издеп жатам",
    "back_menu": "🏠 Менюга",
    "profile_saved": "<b>Бүттү!</b> Анкета жаңыртылды 💜",
    "next": "Кийинки ➡️",
    "like": "💜 Жагат",
    "undo": "⏪ Анкетаны кайтаруу",
    "block": "🚫 Бөгөттөө",
    "report": "⚠️ Шикаят кылуу",
    "open_contact": "💬 Байланышты ачуу",
    "view_likes": "💌 Лайктарды көрүү",
    "view_profile": "💜 Анкетаны көрүү",
    "send_location": "📍 Геолокация жөнөтүү",
    "send_location_placeholder": "Геолокацияны жөнөтүңүз 📍",
    "edit_name": "<b>Жаңы ысым</b>\n2дөн 40 белгиге чейин жөнөтүңүз.",
    "edit_age": "<b>Жаңы жаш</b>\n18ден 99га чейин бүтүн сан жөнөтүңүз.",
    "edit_city": "<b>Жаңы шаар</b>\n2ден 60 белгиге чейин жөнөтүңүз.",
    "edit_bio": "<b>Жаңы сүрөттөмө</b>\n300 белгиге чейин жөнөтүңүз.",
    "edit_gender": "<b>Жынысты тандаңыз</b>",
    "edit_seeking": "<b>Кимди издеп жатасыз?</b>",
    "edit_location": "<b>Жаңы жайгашуу 📍</b>\nТөмөнкү баскыч аркылуу геолокация жөнөтүңүз.",  # noqa: E501
    "edit_photo": "<b>Жаңы сүрөт</b>\nБир сүрөттү фото катары жөнөтүңүз.",
    "age_search_prompt": "<b>Издөө үчүн жаш</b>\nМинималдык жана максималдык жашты боштук менен жөнөтүңүз, мисалы: 20 35.",  # noqa: E501
    "profile_visible": "<b>Анкета кайра көрүнүүдө 💜</b>\nЭми аны башка колдонуучулар көрө алат.",  # noqa: E501
    "profile_hidden": "<b>Анкета жашырылды</b>\nЖаңы колдонуучулар аны издөөдө көрбөйт.",
    "search_saved": "<b>Бүттү!</b> Издөө жөндөөлөрү сакталды 💜",
    "access_restricted": "<b>Кирүү чектелген</b>\n/help, /privacy, /id жана /delete колдоно аласыз.",  # noqa: E501
    "change_language": "🌐 Тилди өзгөртүү",
    "premium_settings": "⚙️ Premium жөндөөлөрү",
    "premium_home": "🏠 Менюга",
    "premium_try": "Сынап көрүү",
    "premium_other": "💎 Башка тариф",
    "premium_terms": "📄 Сатып алуу шарттары",
    "premium_accept": "✅ Шарттарды кабыл алам жана төлөйм",
    "plan_3d": "3 күн",
    "plan_1m": "1 ай",
    "plan_3m": "3 ай",
    "stale_button": "Баскыч эскирген же жараксыз. /start аркылуу улантыңыз.",
    "unknown_message": "Менюден пунктту тандаңыз же /start жөнөтүңүз. /cancel — жокко чыгаруу.",  # noqa: E501
    "pass": "Кийинки ➡️",
    "return_profile": "Анкетаны кайтаруу",
    "block_profile": "Бөгөттөө",
    "report_profile": "Шикаят кылуу",
    "open_contact_short": "Байланышты ачуу",
    "matches_short": "Озара жактыруулар",
    "matches_title_page": "<b>✨ Озара жактыруулар</b>\nБарак {page}",
    "no_matches": "<b>Азырынча озара жактыруу жок 💜</b>\nАнкеталарды көрүңүз — таанышуу бир лайк менен башталышы мүмкүн.",  # noqa: E501
    "name": "Ысым",
    "age": "Жаш",
    "gender": "Жыныс",
    "seeking": "Кимди издеп жатам",
    "location": "Жайгашуу",
    "bio": "Сүрөттөмө",
    "photo": "Сүрөт",
    "hide_profile": "Анкетаны жашыруу",
    "show_profile": "Анкетаны көрсөтүү",
    "delete_profile": "Анкетаны жок кылуу",
    "male": "Эркек",
    "female": "Аял",
    "any": "Маанилүү эмес",
    "caption_distance": "📍 сизден {distance} км",
    "caption_city": "📍 {city}",
    "caption_no_location": "📍 Геолокация",
    "location_city_default": "Геолокация",
    "match_notify": (
        "<b>Сизде озара жактыруу бар! 💜</b>\n\n"
        "Жакыныраак таанышуу үчүн байланышты ачыңыз."
    ),
    "like_notify": (
        "<b>💌 Бирөө сиздин анкетаңызды жактырды</b>\n\n"
        "Кирүүчү лайктарды көрүңүз — балким, жактыруу озара."
    ),
    "temporary_error": "Аракетти аткаруу мүмкүн болбоду. Бир аздан кийин кайра аракет кылыңыз 💜",  # noqa: E501
    "message_send_failed": (
        "Билдирүү же сүрөттү жөнөтүү мүмкүн болбоду. Кайра аракет кылыңыз. "
        "Сүрөт эскирсе, аны «Менин анкетам» бөлүмүндө жаңыртыңыз."
    ),
    "cancel_done": "Аракет жокко чыгарылды. Сакталган анкета өзгөргөн жок.",
    "own_id": "Сиздин Telegram ID: <code>{telegram_id}</code>",
    "delete_confirm": "Ооба, жок кылуу",
    "delete_cancel": "Жокко чыгаруу",
    "delete_stale": "Ырастоо эскирген. /delete менен кайра баштаңыз.",
    "delete_done": (
        "<b>Анкета жок кылынды</b>\n"
        "Тиешелүү реакциялар жана озара жактыруулар жок кылынды. "
        "Модерация жазуулары сакталды."
    ),
    "err_banned": "Сиздин кирүүңүз чектелген. /help, /privacy жана /delete жеткиликтүү.",  # noqa: E501
    "err_rate_limit": "Бир секунд күтүп, кайра басыңыз.",
    "reg_adult_button": "Мага 18 жаш толду",
    "reg_consent_button": "Макулмун",
    "reg_retry_username": "Кайра текшерүү",
    "reg_name_prompt": (
        "<b>Атыңыз ким?</b>\n"
        "Анкета үчүн ысым жазыңыз: 2дөн 40 белгиге чейин.\n\n"
        "<i>Байланышсыз жана шилтемесиз. /cancel — жокко чыгаруу.</i>"
    ),
    "reg_age_prompt": "<b>Жашыңыз канчада?</b>\nЖашты 18–99 аралыгында бүтүн сан катары жөнөтүңүз.",  # noqa: E501
    "reg_gender_prompt": "<b>Жынысыңызды көрсөтүңүз</b>",
    "reg_seeking_prompt": "<b>Кимди издеп жатасыз?</b>",
    "reg_location_prompt": (
        "<b>Кайда жайгашкансыз? 📍</b>\n"
        "Төмөнкү баскыч аркылуу геолокация жөнөтүңүз. Алгач сизге жакыныраак "
        "адамдарды, анан алыскыларды көрсөтөбүз.\n\n"
        "<i>Так координаттар башка колдонуучуларга көрсөтүлбөйт.</i>"
    ),
    "reg_bio_prompt": (
        "<b>Өзүңүз жөнүндө жазыңыз</b>\n"
        "300 белгиге чейин жазыңыз же бул кадамды өткөрүп жибериңиз.\n\n"
        "<i>@username жана шилтемелерди көрсөтпөңүз.</i>"
    ),
    "reg_skip_button": "Өткөрүп жиберүү",
    "reg_photo_prompt": (
        "<b>Сүрөт кошуңуз</b>\n"
        "Бир өз сүрөтүңүздү Telegramда фото катары жөнөтүңүз.\n\n"
        "<i>Файл же видео ылайыктуу эмес.</i>"
    ),
    "reg_confirm_button": "Ырастоо",
    "reg_restart_button": "Кайра толтуруу",
    "reg_done": (
        "<b>Бүттү! Анкета түзүлдү 💜</b>\n"
        "Издөө 18–99 жашка жөндөлдү. Анкеталар жакыныраактардан баштап "
        "көрсөтүлөт. Геолокацияны жөндөөлөрдө өзгөртө аласыз."
    ),
    "reg_wrong_photo": (
        "Бир сүрөттү фото катары жөнөтүңүз. Видео, файл жана текст ылайыктуу эмес.\n\n"
        "<i>/cancel — жокко чыгаруу.</i>"
    ),
    "reg_wrong_input": (
        "Учурдагы суроого жооп бериңиз же ылайыктуу баскычты басыңыз. "
        "/cancel — жокко чыгаруу, /start — кайра баштоо."
    ),
    "intro": (
        "<b>💜 Рядом</b>\n"
        "Сиздин окуяңыз бир таанышуудан башталат.\n\n"
        "Анкета түзүңүз, жакын айланадагы адамдарды көрүңүз жана озара "
        "жактырууну табыңыз.\n\n"
        "<i>18 жаштан жогорку колдонуучулар үчүн гана. Жаш өз алдынча "
        "көрсөтүлөт; документтер текшерилбейт.</i>"
    ),
    "consent": (
        "<b>Макулдук жана купуялык</b>\n\n"
        "Ырастагандан кийин сиздин анкетаңызды — ысым, жаш, жыныс, сүрөттөмө "
        "жана сүрөт — башка колдонуучулар көрөт. Озара жактыруудан кийин "
        "колдонуучу сиздин Telegram username'иңизди ача алат. Геолокация "
        "масофени эсептөө үчүн гана керек жана башкаларга көрсөтүлбөйт.\n\n"
        "Бот телефон, сырсөз, паспорт же так даректи сурабайт. Ысым же "
        "сүрөттөмөдө @username жана шилтемелерди көрсөтпөңүз. Кеңири: /privacy.\n\n"
        "<b>Макулсузбу?</b>"
    ),
    "username_help": (
        "<b>Telegram username кошуңуз</b>\n\n"
        "Telegram → Жөндөөлөр → Профилди өзгөртүү → Колдонуучу аты. Анан бул "
        "жерге кайтып «Кайра текшерүү» баскычын басыңыз.\n\n"
        "<i>Username'ди бул чатка жөнөтпөңүз.</i>"
    ),
    "help": (
        "<b>❔ Жардам</b>\n\n"
        "Анкеталарды көрүңүз, 💜 басыңыз жана озара жактырууда байланышты "
        "ачыңыз. Маектешүү Telegram жеке чатында уланат — ботто анонимдик чат жок.\n\n"
        "Бот 18 жаштан жогорку адамдар үчүн гана. Спам, жасалма анкеталар жана "
        "жарамсыз мазмун тыюу салынат. Шектүү анкетаны бөгөттөй аласыз же шикаят "
        "жөнөтө аласыз. Сырсөз, акча же документтерди бербеңиз.\n\n"
        "/start — меню же каттоо\n"
        "/privacy — купуялык\n"
        "/cancel — учурдагы аракетти жокко чыгаруу\n"
        "/id — сиздин Telegram ID\n"
        "/delete — анкетаны жок кылуу\n\n"
        "<i>Бүтпеген анкета кайра иштетилгенден кийин жоголушу мүмкүн; "
        "даяр анкета сакталат.</i>"
    ),
    "privacy": (
        "<b>🔐 Купуялык</b>\n\n"
        "Анкета ырасталгандан кийин гана көрүнөт. Бот Telegram ID, username, "
        "анкета, координаттар, издөө жөндөөлөрү, макулдук убактысы, чечимдер, "
        "озара жактыруулар, бөгөттөөлөр жана шикаяттарды сактайт. Сүрөттүн "
        "file_id сакталат; сүрөттүн өзү сервердин дискына жүктөлбөйт. Геолокация "
        "масофа боюнча иреттөө үчүн колдонулат жана башкаларга көрсөтүлбөйт. "
        "Байланыш озара жактырууда гана ачылат.\n\n"
        "Анкетаны жашыруу жаңы издөөнү жана лайк алууну токтотот; мурунку озара "
        "жактыруулар сакталат. Бөгөттөө боттогу көрүнүүнү жана байланышка "
        "жетүүнү чектейт, бирок Telegram жеке чатын бөгөттөбөйт. Шикаяттарды "
        "администраторлор көрөт; шикаят авторы ачыкка чыгарылбайт. Администратор "
        "шикаяттарды жана учурдагы анкетаны көрүп, колдонуучуларды бөгөттөй алат.\n\n"
        "Жок кылуу: /delete.\n\n"
    ),
    "delete_notice": (
        "<b>🗑 Анкетаны жок кылуу</b>\n\n"
        "Ысым, жаш, жыныс, геолокация, сүрөттөмө, сүрөттүн file_id, издөө "
        "жөндөөлөрү, макулдук жана анкета түзүлгөн убакыт, тиешелүү реакциялар "
        "жана озара жактыруулар жок кылынат. Сакталган username да тазаланат.\n\n"
        "Модерация үчүн ички ID, Telegram ID, бөгөттөө статусу, аккаунт "
        "түзүлгөн убакыт, бөгөттөөлөр — эки тараптын ID'си жана убакыт — жана "
        "шикаяттар — эки тараптын ID'си, себеби же комментарийи, статусу, "
        "убактысы жана текшерген администратордун ID'си — сакталат. Учурдагы "
        "username кийинки билдирүүдө жаңыртылышы мүмкүн. Telegram'дагы эски "
        "билдирүүлөрдү жана мурун ачылган байланыштарды кайтарып алуу мүмкүн эмес.\n\n"
        "<b>Анкетаны так жок кыласызбы?</b>"
    ),
    "err_invalid_button": "Баскыч эскирген же жараксыз.",
    "err_profile_not_found": "Анкета табылган жок.",
    "err_profile_not_found_start": "Анкета табылган жок. /start жөнөтүңүз.",
    "err_profile_deleted": "Анкета жок кылынды.",
    "err_create_profile": "Алгач /start аркылуу анкета түзүңүз.",
    "err_two_ints": "Эки бүтүн сан жөнөтүңүз, мисалы: 20 35.",
    "err_ints_expected": "Жаш эки бүтүн сан менен көрсөтүлүшү керек, мисалы: 20 35.",  # noqa: E501
    "err_send_text_or_cancel": "Текст жөнөтүңүз же /cancel колдонуңуз.",
    "err_use_buttons_above": "Жогорку баскычтар аркылуу вариантты тандаңыз.",
    "err_button_unavailable": "Бул баскыч азыр жеткиликсиз.",
    "err_profile_field_missing": "Анкета же талаа табылган жок.",
    "err_location_button": "Төмөнкү баскыч аркылуу геолокация жөнөтүңүз.",
    "err_one_photo_photo": "Бир сүрөттү фото катары жөнөтүңүз, файл же видео эмес.",  # noqa: E501
    "err_message_unavailable": "Билдирүү жеткиликсиз.",
    "err_invalid_command": "Буйрук туура эмес.",
    "err_choose_reason": "Себепти баскыч аркылуу тандаңыз.",
    "err_comment_length": "Комментарий 1–300 белгиден болушу керек.",
    "edit_cancel_hint": "\n\n<i>/cancel — сактабастан жокко чыгаруу.</i>",
    "edit_clear_bio": "Сүрөттөмөнү тазалоо",
    "no_undo_profile": "Кайтаруу үчүн анкета жок. Акыркы анкета өткөрүп жиберилген болушу керек.",  # noqa: E501
    "photo_counter": "Сүрөт {position}",
    "decision_saved": "Бул анкета боюнча чечимиңиз мурун сакталган.",
    "matches_prev": "← Артка",
    "matches_next": "Кийинки →",
    "contact_opened": (
        "<b>💬 Байланыш ачылды</b>\n{url}\n\n"
        "Маектешүү Telegram жеке чатында уланат."
    ),
    "contact_unavailable": (
        "<b>Байланыш азырынча жеткиликсиз</b>\n"
        "Колдонуучудан Telegram username кошууну суранып, кийин кайра аракет кылыңыз."
    ),
    "contact_retry": "Кайра аракет кылуу",
    "reason_spam": "Спам",
    "reason_fake": "Жасалма анкета",
    "reason_content": "Жарамсыз мазмун",
    "reason_other": "Башка",
    "reason_other_value": "Башка: {value}",
    "report_reason_prompt": "<b>Эмнеге шикаят кылгыңыз келет?</b>\nТөмөнөн себепти тандаңыз.\n\n<i>/cancel — жокко чыгаруу.</i>",  # noqa: E501
    "report_confirm_prompt": (
        "<b>Шикаят жөнөтөсүзбү?</b>\n"
        "Аны администраторлор көрөт, ал эми анкета сиз үчүн бөгөттөлөт. "
        "Колдонуучу шикаятты ким жөнөткөнүн билбейт."
    ),
    "report_send": "Шикаят жөнөтүү",
    "report_comment_prompt": (
        "<b>Себепти сүрөттөңүз</b>\n"
        "1ден 300 белгиге чейин комментарий жазыңыз.\n\n"
        "<i>/cancel — жокко чыгаруу.</i>"
    ),
    "report_saved": "<b>Шикаят сакталды</b>\nАнкета сиз үчүн бөгөттөлдү.",
    "blocked_notice": (
        "<b>Колдонуучу бөгөттөлдү</b>\n"
        "Анкеталар бири-бирине ботто көрүнбөйт, ал эми байланыш жеткиликсиз болот.\n\n"
        "<i>Telegram жеке чатында колдонуучуну өзүнчө бөгөттөй аласыз.</i>"
    ),
    "err_text_length": "Текст {minimum}–{maximum} белгиден болушу керек.",
    "err_no_contacts": "Байланыштарды, @username жана шилтемелерди көрсөтпөңүз.",
    "err_age_invalid": "Жаш 18ден 99га чейин болушу керек. Кайра аракет кылыңыз 💜",
    "err_min_max": "Минималдык жаш максималдыктан чоң болбошу керек.",
    "err_location_failed": "Геолокацияны аныктоо мүмкүн болбоду. Кайра аракет кылыңыз.",
    "err_user_not_found": "Колдонуучу табылган жок.",
    "err_access_limited": "Кирүү чектелген. /help, /privacy жана /delete жеткиликтүү.",
    "err_create_or_show_profile": "Алгач анкета түзүңүз же аны кайра көрүнүүчү кылыңыз.",  # noqa: E501
    "err_add_username": "Telegram жөндөөлөрүндө колдонуучу атын кошуңуз.",
    "err_profile_stale": "Анкета маалыматтары эскирген. /start менен кайра баштаңыз.",
    "err_photo_and_consent": "Сүрөт жана макулдук керек. /start менен кайра баштаңыз.",  # noqa: E501
    "err_invalid_field": "Жараксыз талаа же маани.",
    "err_create_profile_start": "Алгач анкета түзүңүз: /start",
    "err_profile_and_username": "Анкета жана Telegram колдонуучу аты керек.",
    "err_likes_limit": (
        "{limit} лайк лимити бүттү.\n"
        "Кийинки жаңылануу: {reset_at} UTC.\n\n"
        "💎 Premium лайк лимитин алып салат."
    ),
    "err_undo_limit": (
        "Анкетаны кайтаруу суткасына {limit} жолу жеткиликтүү.\n"
        "Кийинки жаңылануу: {reset_at} UTC.\n\n"
        "💎 Premium кайтаруу лимитин алып салат."
    ),
    "err_invalid_reaction": "Жараксыз реакция.",
    "err_profile_unavailable": "Бул анкета азыр жеткиликсиз же сиздин фильтрлерге ылайык келбейт.",  # noqa: E501
    "err_match_unavailable": "Озара жактыруу табылган жок же сиз үчүн жеткиликсиз.",
    "err_match_unavailable_now": "Бул озара жактыруу азыр жеткиликсиз.",
    "err_invalid_page": "Жараксыз барак.",
    "err_invalid_profile": "Жараксыз анкета.",
    "err_profile_action_unavailable": "Бул анкета менен аракет жеткиликсиз.",
    "err_report_comment": "Шикаят комментарийи өтө узун же бош.",
    "err_admin_only": "Бул бөлүм администратор үчүн гана жеткиликтүү.",
    "err_report_not_found": "Шикаят табылган жок.",
    "err_invalid_action": "Жараксыз аракет же шикаят.",
    "err_send_start": "Алгач /start жөнөтүңүз.",
    "err_invalid_premium_plan": "Жараксыз Premium планы.",
    "err_premium_event": "Premium окуясы мурун иштетилген.",
    "err_photo_limit": "Сүрөт лимитине жеттиңиз ({limit}).",
    "err_photo_limit_premium": (
        "Сүрөт лимитине жеттиңиз ({limit}).\n\n"
        "💎 Premium {premium_limit} сүрөткө чейин кошууга мүмкүндүк берет."
    ),
    "err_last_photo": "Жалгыз сүрөттү жок кылуу мүмкүн эмес. Алгач башкасын кошуңуз.",
    "err_photo_not_found": "Сүрөт табылган жок.",
    "err_boost_premium": "Boost Premium менен гана жеткиликтүү.",
    "err_boost_cooldown": (
        "Boostту {hours} сааттан кийин кайра активдештирүүгө болот.\n"
        "Кийинки активдештирүү: {next_at} UTC."
    ),
    "err_invalid_sort": "Жараксыз иреттөө.",
    "err_incoming_premium": "Кирүүчү лайктардын тизмеси Premium менен гана жеткиликтүү.",  # noqa: E501
    "no_profiles": (
        "<b>Азыр ылайыктуу анкеталар жок 💜</b>\n"
        "Издөө жөндөөлөрүн өзгөртүп көрүңүз же кийин кириңиз."
    ),
    "no_likes": "<b>Азырынча жаңы лайктар жок 💌</b>\nАзырынча анкеталарды көрө аласыз.",  # noqa: E501
    "trial_welcome": (
        "🎁 Сизге {days} күнгө Premium акысыз жеткиликтүү!\n\n"
        "Бардык Premium мүмкүнчүлүктөрү мурун активдештирилген.\n"
        "Мөөнөтү: {until} чейин"
    ),
    "trial_reminder": (
        "⏳ Акысыз Premium эртең бүтөт.\n"
        "Бардык мүмкүнчүлүктөргө жетүүнү сактоо үчүн Premiumду улантыңыз."
    ),
    "trial_expired": (
        "⌛ Акысыз Premium бүттү.\n"
        "Ботту акысыз колдонууну уланта аласыз же Premium туташтыра аласыз."
    ),
    "boost_activated": (
        "<b>🚀 Анкетаңыз көтөрүлдү!</b>\n\n"
        "{minutes} мүнөткө жарактуу. Анкетаңыз ылайыктуу талапкерлердин "
        "арасында артыкчылык менен көрсөтүлөт.\n\n"
        "Кийинки көтөрүү жеткиликтүү: {next_at}"
    ),
    "boost_active": (
        "<b>🚀 Көтөрүү мурун активдүү</b>\n\n"
        "Калды: {minutes} мүн.\n"
        "Кийинки көтөрүү жеткиликтүү: {next_at}"
    ),
    "boost_cooldown": (
        "<b>🚀 Анкетаны көтөрүү</b>\n\n"
        "Кийинки көтөрүү жеткиликтүү: {next_at}\n\n"
        "Көтөрүү 30 мүнөткө көрсөтүүдө артыкчылык берет жана суткасына бир "
        "жолу жеткиликтүү."
    ),
    "premium_intro": (
        "<b>💎 Premium — таанышуу мүмкүнчүлүгү көбүрөөк</b>\n"
        "<i>Мүмкүнчүлүктөрдү салыштырып, өзүңүзгө ылайыктуусун тандаңыз.</i>\n\n"
        "<b>Кадимки аккаунт  →  Premium</b>\n\n"
        "💜 <b>Суткасына лайктар</b>\n"
        "30  →  <b>чектоосуз</b>\n\n"
        "↩️ <b>Анкетаны кайтаруу</b>\n"
        "суткасына 1  →  <b>чектоосуз</b>\n\n"
        "📸 <b>Анкетадагы сүрөттөр</b>\n"
        "1 сүрөт  →  <b>5 сүрөткө чейин</b>\n\n"
        "📍 <b>Так издөө радиусу</b>\n"
        "кадимки издөө  →  <b>10 / 25 / 50 / 100 км</b>\n\n"
        "💌 <b>Кирүүчү лайктар</b>\n"
        "бир-биринен  →  <b>тизме жана иреттөө</b>\n\n"
        "🚀 <b>Анкетаны Boost кылуу</b>\n"
        "жеткиликсиз  →  <b>суткасына бир жолу 30 мүнөткө көтөрүү</b>\n\n"
        "Ошондой эле анкетадагы көзгө көрүнгөн <b>💎 Premium</b> белгиси.\n\n"
        "<b>Premium мөөнөтүн тандаңыз:</b>"
    ),
    "premium_active": (
        "<b>💎 Сизде Premium бар</b>\n"
        "<i>Бардык кеңейтилген мүмкүнчүлүктөр мурун жеткиликтүү.</i>\n\n"
        "🗓 Мөөнөтү: <b>{until}</b> чейин\n"
        "⏳ Калган күндөр: <b>{days}</b>\n\n"
        "<b>Эмне кирет:</b>\n"
        "∞ лайктар жана анкетаны кайтаруу\n"
        "📸 5 сүрөткө чейин\n"
        "📍 радиус 10 / 25 / 50 / 100 км\n"
        "💌 иреттөө менен кирүүчү лайктардын тизмеси\n"
        "🚀 Анкетаны 30 мүнөткө Boost кылуу\n"
        "💎 анкетадагы Premium белгиси\n\n"
        "<b>Premiumду улантуу:</b>"
    ),
    "premium_trial_active": (
        "<b>🎁 Сынак Premium {until} чейин активдүү</b>\n\n"
        "Бардык Premium мүмкүнчүлүктөрү мурун активдештирилген.\n\n"
        "Жетүүнү алдын ала уланта аласыз — төлөнгөн мөөнөт сынак мезгилинен "
        "кийин башталат."
    ),
    "premium_paid_active": (
        "<b>💜 Premium {until} чейин активдүү</b>\n\n"
        "Бардык Premium мүмкүнчүлүктөрү мурун активдештирилген.\n\n"
        "Жаңы төлөнгөн мөөнөт учурдагы калдыкка кошулат."
    ),
    "premium_not_connected": (
        "<b>Төлөм азырынча туташтырылган эмес</b>\n\n"
        "Premium функциялары толугу менен иштелген, бирок Telegram Stars аркылуу "
        "төлөм кабыл алуу кийинки этапта туташтырылат.\n\n"
        "Администратор тестирлөө үчүн Premiumду бул буйрук менен бере алат:\n"
        "<code>/premium_grant TELEGRAM_ID premium_1m</code>"
    ),
    "premium_plan_details": (
        "<b>💎 {plan} үчүн Premium</b>\n\n"
        "Баасы: <b>{price} ⭐️</b>\n"
        "Мөөнөтү: <b>{plan}</b>\n"
        "Сатып алуу түрү: <b>бир жолу, авточегерүүсүз</b>\n\n"
        "Жаңы мөөнөт мурун төлөнгөн калдыкка кошулат. Төмөнкү баскычты басуу "
        "менен /terms шарттарын кабыл аласыз."
    ),
    "premium_settings_text": (
        "<b>⚙️ Premium жөндөөлөрү</b>\n\n"
        "💎 белгиси: {badge}\n\n"
        "Жөндөө күйгүзүлсө, белги сиздин анкетаңызда көрсөтүлөт."
    ),
    "premium_badge_shown": "көрсөтүлүүдө",
    "premium_badge_hidden": "жашырылган",
    "premium_badge_show_button": "💎 белгисин көрсөтүү",
    "premium_badge_hide_button": "💎 белгисин жашыруу",
    "premium_badge_done": "<b>Бүттү!</b> Анкетаңыздагы 💎 белгиси {badge}.",
    "err_premium_only": "Бул функция Premium колдонуучулар үчүн гана жеткиликтүү.",
    "err_invalid_tariff": "Жараксыз тариф.",
    "err_sales_paused": "Жаңы Premium сатып алуулар убактылуу токтотулду.",
    "err_purchase_unavailable": "Premium сатып алуу азыр жеткиликсиз.",
    "err_order_not_found_owner": "Заказ табылган жок же башка колдонуучуга таандык.",  # noqa: E501
    "err_order_closed": "Бул заказ мурун жабылган. Тарифти кайра тандаңыз.",
    "err_order_expired": "Заказды күтүү убактысы бүттү. Тарифти кайра тандаңыз.",
    "err_unknown_order": "Белгисиз заказ. Premium бөлүмүндө жаңы эсеп түзүңүз.",
    "err_order_no_invoice": "Заказ табылган жок. Premium бөлүмүндө жаңы эсеп түзүңүз.",  # noqa: E501
    "err_invoice_other_user": "Бул эсеп башка колдонуучу үчүн түзүлгөн.",
    "err_invoice_amount": "Эсептин суммасы заказга дал келген жок. Төлөм токтотулду.",  # noqa: E501
    "err_invoice_not_ready": "Заказ мурун жабылган же төлөмгө даяр эмес.",
    "err_confirm_terms_first": "Алгач боттогу сатып алуу шарттарын ырастаңыз.",
    "err_invoice_expired": "Эсепти күтүү убактысы бүттү. Жаңы заказ түзүңүз.",
    "err_checkout_failed": "Заказды текшерүү мүмкүн болбоду. Жаңы эсеп түзүп көрүңүз.",
    "err_order_not_found": "Заказ табылган жок.",
    "err_no_refundable_payment": "Бул заказ үчүн кайтарууга жеткиликтүү төлөм жок.",
    "err_invalid_payment_button": "Жараксыз төлөм баскычы.",
    "err_no_refund": "Бул төлөмдү кайтаруу мүмкүн эмес.",
    "err_invalid_payment_action": "Төлөм менен жараксыз аракет.",
    "refund_unknown": (
        "Кайтаруунун натыйжасы белгисиз. Аны сокур түрдө кайталабаңыз: "
        "/stars_reconcile иштетиңиз."
    ),
    "err_refund_not_confirmed": "Telegram кайтарууну ырастаган жок. Салыштырууну аткарыңыз.",  # noqa: E501
    "payment_success": (
        "<b>✅ Төлөм алынды — Premium активдештирилди</b>\n\n"
        "Заказ: <code>{order}</code>\n"
        "Жетүү <b>{until}</b> чейин жарактуу\n\n"
        "Рахмат! Premiumду 💎 Premium баскычы аркылуу башкара аласыз."
    ),
    "invoice_already_sent": "Эсеп мурун жогору жөнөтүлгөн. Аны ачып, төлөм баскычын басыңыз.",  # noqa: E501
    "invoice_sending": "Эсеп мурун түзүлүүдө. Бир нече секунд күтүңүз.",
    "invoice_title": "Premium «Рядом»: {plan}",
    "invoice_description": (
        "{plan} үчүн Premiumду бир жолу сатып алуу. Авточегерүүсүз жана "
        "автоматтык улантуусуз."
    ),
    "invoice_label": "{plan} үчүн Premium",
    "invoice_error": (
        "Эсепти жөнөтүү мүмкүн болбоду. Сатып алуу болбоду, Stars чегерилген жок. "
        "Төлөм баскычын кайра басып көрүңүз."
    ),
    "payment_review": (
        "Төлөм алынды, бирок параметрлер текшерүүнү талап кылат. Premium автоматтык "
        "түрдө берилген жок. /paysupport жөнөтүңүз — администратор төлөмдү көрөт."
    ),
    "refund_ack": (
        "<b>Stars кайтаруу эсепке алынды</b>\n\n"
        "Кайтарылган сатып алуу боюнча жетүү оңдолду. Башка сатып алуулар жана "
        "административдик берүүлөр сакталды."
    ),
    "paysupport_admin": (
        "<b>💳 Төлөм боюнча кайрылуу</b>\n"
        "Колдонуучу: <code>{telegram_id}</code>\n"
        "Заказ: <code>{order}</code>\n"
        "Статус: {status}"
    ),
    "paysupport_none": "табылган жок",
    "paysupport_no_order": "заказ жок",
    "paysupport_sent": (
        "<code>{order}</code> заказы боюнча кайрылуу администраторлорго өткөрүлдү. "
        "Алар төлөмдү текшерип, керек болсо Stars кайтарышат."
    ),
    "paysupport_failed": (
        "Кайрылууну администраторлорго жеткирүү мүмкүн болбоду. Кийин аракет "
        "кылыңыз. Заказ номерин сактаңыз: <code>{order}</code>."
    ),
    "refund_button": "Stars кайтаруу",
    "payadmin_title": "<b>💳 Premium заказдары</b>\nБарак {page}",
    "payadmin_order": (
        "<b>💳 Premium заказ</b>\n"
        "Номери: <code>{order}</code>\n"
        "Колдонуучу: <code>{buyer}</code>\n"
        "Тариф: {plan}\n"
        "Сумма: {price} {currency}\n"
        "Заказ статусу: {status}\n"
        "Төлөм статусу: {payment_status}"
    ),
    "payadmin_no_payment": "жок",
    "payadmin_back": "💳 Заказдарга",
    "refund_confirm_prompt": (
        "<b>Кайтарууну ырастаңыз</b>\n"
        "Колдонуучу: <code>{buyer}</code>\n"
        "Сумма: <b>{price} ⭐️</b>\n"
        "Заказ: <code>{order}</code>"
    ),
    "refund_yes": "Ооба, Stars кайтаруу",
    "refund_done": "<b>Кайтаруу аткарылды</b>\nStars кайтарылды, жетүү оңдолду.",
    "reconcile_done": (
        "<b>Stars салыштыруу аяктады</b>\n"
        "Кирүүчү эсептер: {incoming}\n"
        "Кайтаруулар: {refunded}\n"
        "Башка операциялар: {skipped}"
    ),
    "err_no_sender": "Буйруктун жөнөтүүчүсүн аныктоо мүмкүн болбоду.",
    "admin_panel": (
        "<b>🛡 Администратор панели</b>\n"
        "Колдонуучулар: {users}\n"
        "Активдүү анкеталар: {profiles}\n"
        "Озара жактыруулар: {matches}\n"
        "Ачык шикаяттар: {reports}\n\n"
        "/ban Telegram_ID — бөгөттөө\n"
        "/unban Telegram_ID — бөгөттөөнү алуу"
    ),
    "admin_reports_button": "⚠️ Шикаяттар",
    "err_ban_usage": "Буйруктан кийин Telegram ID көрсөтүңүз: /ban 123456789",
    "admin_banned": "Колдонуучу бөгөттөлдү.",
    "admin_unbanned": "Бөгөттөө алынды. Анкета автоматтык түрдө активдешпейт.",
    "err_grant_usage": "Формат: /premium_grant TELEGRAM_ID PLAN_CODE",
    "err_grant_plan_usage": (
        "Формат: /premium_grant TELEGRAM_ID PLAN_CODE\n"
        "План: premium_3d, premium_1m, premium_3m"
    ),
    "err_plan_invalid": "План premium_3d, premium_1m же premium_3m болушу керек",
    "admin_granted": (
        "<b>Premium берилди</b>\n"
        "Колдонуучу: <code>{telegram_id}</code>\n"
        "План: {plan}\n"
        "Мөөнөтү: {until} чейин"
    ),
    "err_status_usage": "Формат: /premium_status TELEGRAM_ID",
    "admin_status": (
        "<b>Premium статусу</b>\n"
        "Колдонуучу: <code>{telegram_id}</code>\n"
        "Статус: {status}{details}"
    ),
    "admin_status_active": "Активдүү",
    "admin_status_none": "Premium жок",
    "admin_status_until": "\nМөөнөтү: {until} чейин\nКалган күндөр: {days}",
    "err_revoke_usage": "Формат: /premium_revoke TELEGRAM_ID",
    "admin_revoked": "<b>Premium артка алынды</b>\nКолдонуучу: <code>{telegram_id}</code>",
    "err_admin_button": "Администратордун жараксыз баскычы.",
    "err_admin_message": "Администратордун билдирүүсү жеткиликсиз.",
    "admin_report_row": "Шикаят #{report_id}",
    "admin_reports_page": "<b>⚠️ Ачык шикаяттар</b>\nБарак {page}",
    "admin_no_reports": "<b>Ачык шикаяттар жок</b>",
    "admin_block_button": "Бөгөттөө",
    "admin_unblock_button": "Бөгөттөөнү алуу",
    "admin_reviewed_button": "Каралды",
    "admin_report_detail": (
        "<b>Шикаят #{report_id}</b>\nСебеби: {reason}\nСтатусу: {status}"
    ),
    "admin_report_open": "ачык",
    "admin_report_closed": "каралды",
    "admin_profile_deleted": "Учурдагы анкета жок кылынды, бирок модерация жазуусу сакталды.",  # noqa: E501
    "admin_action_done": (
        "<b>Аракет аткарылды</b>\n"
        "Бөгөттөөнү алуу анкетаны автоматтык түрдө активдештирбейт."
    ),
    "err_admin_action": "Администратордун жараксыз аракети.",
    "err_language_invalid": "Тилди тандоо мүмкүн болбоду. Кайра аракет кылыңыз.",
    "err_album_not_allowed": "Бир гана сүрөт жөнөтүңүз, альбомсуз.",
    "err_choose_gender": "Жогорку баскычтар аркылуу жынысты тандаңыз.",
    "err_choose_button": "Жогорку баскычтар аркылуу вариантты тандаңыз.",
    "payment_terms": (
        "<b>📄 Premium сатып алуу шарттары</b>\n\n"
        "Premium — «Рядом» ботунун ичиндеги төлөмдүү жетүү жана Telegram Premium "
        "жазылуусу эмес. Сатып алуу бир жолу: автоматтык чегерүү жана автоматтык "
        "улантуу жок.\n\n"
        "Тариф мөөнөтү кечирээк датага кошулат: учурдагы убакытка, trial "
        "аяктаганга же учурдагы төлөнгөн Premiumга. 3 күндүк тариф 72 саат "
        "жарактуу; айлык тарифтер календардык айлар деп эсептелип, айдын "
        "акыркы күнүнө өткөрүлөт.\n\n"
        "Төлөм Telegram Stars аркылуу жүргүзүлөт. Premium Telegram ийгиликтүү "
        "төлөм тууралуу кабарлагандан кийин гана берилет. Эсепти жокко чыгаруу "
        "учурдагы жетүүнү өзгөртпөйт.\n\n"
        "Төлөм боюнча суроо же кайтаруу өтүнүчү үчүн /paysupport жөнөтүңүз. "
        "Заказ номерин билсеңиз, көрсөтүңүз. Кайтарууну администратор карап, "
        "Telegram аркылуу аткарат."
    ),
    "cmd_start": "Меню жана каттоо",
    "cmd_help": "Жардам",
    "cmd_privacy": "Купуялык",
    "cmd_terms": "Premium сатып алуу шарттары",
    "cmd_paysupport": "Төлөм боюнча колдоо",
    "cmd_cancel": "Аракетти жокко чыгаруу",
    "cmd_id": "Менин Telegram ID",
    "cmd_delete": "Анкетаны жок кылуу",
}

TRANSLATIONS: Final[dict[str, dict[str, str]]] = {
    "ru": {
        "welcome": (
            "<b>👋 Привет!</b>\n\n🌍 <b>Рядом</b> — здесь можно найти новые знакомства.\n\n"
            "Выбери язык, чтобы продолжить:"
        ),
        "language_selected": "<b>🌐 Язык выбран: Русский</b>\n\nПриятного общения!",
        "continue": "Продолжить",
        **_COMMON,
        **_RU_EXTRA,
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
    "kg": {
        "welcome": (
            "<b>👋 Салам!</b>\n\n🌍 <b>Рядом</b> — бул жерден жаңы таанышууларды "
            "таба аласыз.\n\nУлантуу үчүн тилди тандаңыз:"
        ),
        "language_selected": "<b>🌐 Тил тандалды: Кыргызча</b>\n\nЖакшы маектешүү!",
        "continue": "Улантуу",
        **_KG,
    },
}


def normalize_language(language: str | None) -> str:
    value = (language or "").strip().lower()
    return value if value in LANGUAGES else DEFAULT_LANGUAGE


def language_from_code(code: str | None) -> str | None:
    """Map a Telegram client language code (e.g. "en-US", "uz") to a supported language."""
    base = (code or "").strip().lower().replace("_", "-").split("-", 1)[0]
    base = _LANGUAGE_ALIASES.get(base, base)
    return base if base in LANGUAGES else None


def localized_labels(key: str) -> set[str]:
    from bot.texts import MENU_LABEL_ALIASES

    indexes = {
        "menu_discover": 0,
        "menu_profile": 1,
        "menu_likes": 2,
        "menu_matches": 3,
        "menu_settings": 4,
        "menu_premium": 5,
        "menu_help": 6,
    }
    values = {translations[key] for translations in TRANSLATIONS.values()}
    values.update(MENU_LABEL_ALIASES[indexes[key]])
    return values


def tr(key: str, language: str | None = None, **format_values: object) -> str:
    language = normalize_language(language or current_language.get())
    translations = TRANSLATIONS[language]
    value = translations.get(key)
    if value is None:
        value = TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key)
    return value.format(**format_values) if format_values else value
