"""Legacy reply-keyboard labels kept for alias matching.

All user-visible bot text lives in the ``bot.i18n`` lexicon and is resolved per
user language. Only the historical keyboard labels (needed to route buttons that
older clients still show) and the Russian fallback constant referenced by
regression tests remain here.
"""

MENU_LABELS = (
    "💜 Смотреть анкеты",
    "👤 Моя анкета",
    "💌 Лайки",
    "✨ Взаимные симпатии",
    "⚙️ Настройки",
    "💎 Premium",
    "❔ Помощь",
)

# Reply keyboards remain in Telegram chats after an interface update. Keep every
# previously shipped Russian and Uzbek label routable until a new /start replaces it.
PREVIOUS_MENU_LABELS = (
    "🔎 Смотреть анкеты",
    "👤 Моя анкета",
    "❤️ Мне поставили лайк",
    "🤝 Мои взаимные симпатии",
    "⚙️ Настройки поиска",
    "💎 Premium",  # Added for compatibility
    "❓ Помощь",
)
LEGACY_MENU_LABELS = (
    "🔎 Anketalarni ko'rish",
    "👤 Mening anketam",
    "❤️ Menga like bosganlar",
    "🤝 Matchlarim",
    "⚙️ Qidiruv sozlamalari",
    "💎 Premium",  # Added for compatibility
    "❓ Yordam",
)
MENU_LABEL_ALIASES = tuple(
    frozenset((current, previous, legacy))
    for current, previous, legacy in zip(
        MENU_LABELS, PREVIOUS_MENU_LABELS, LEGACY_MENU_LABELS, strict=True
    )
)

# Russian fallback for unexpected errors; must equal tr("temporary_error", "ru")
# because AccessMiddleware serves tr("temporary_error") to users.
TEMPORARY_ERROR = "Не получилось выполнить действие. Попробуй ещё раз чуть позже 💜"
