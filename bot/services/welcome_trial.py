"""Delivery of persistent one-time welcome-trial notifications."""

import logging

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from bot.i18n import tr
from bot.keyboards.common import discovery_reminder as discovery_reminder_keyboard
from bot.services.store import Store, TrialNotification
from bot.services.telegram import safe_call

logger = logging.getLogger(__name__)


async def send_discovery_reminder(bot: Bot, store: Store, telegram_id: int) -> bool:
    """Send the localized text-only discovery reminder to one Telegram user."""
    language = await store.language_of(telegram_id)
    sent = await safe_call(
        store,
        telegram_id,
        lambda: bot.send_message(
            telegram_id,
            tr("discovery_reminder", language),
            reply_markup=discovery_reminder_keyboard(language),
        ),
    )
    return sent is not None


def notification_text(notification: TrialNotification, language: str | None = None) -> str:
    language = language or notification.language
    if notification.kind == "welcome":
        duration_days = (notification.trial_ends_at - notification.trial_started_at).days
        return tr(
            "trial_welcome",
            language,
            days=duration_days,
            until=notification.trial_ends_at.strftime("%d.%m.%Y %H:%M UTC"),
        )
    if notification.kind == "reminder":
        return tr("trial_reminder", language)
    return tr("trial_expired", language)


async def deliver_trial_notifications(bot: Bot, store: Store, *, user_id: int | None = None) -> int:
    """Claim and send due notices, returning the number accepted by Telegram."""
    delivered = 0
    for notification in await store.claim_trial_notifications(user_id=user_id):
        try:
            await bot.send_message(notification.telegram_id, notification_text(notification))
        except TelegramAPIError as exc:
            logger.info(
                "Не доставлено уведомление trial; вид=%s ошибка=%s",
                notification.kind,
                type(exc).__name__,
            )
            continue
        delivered += 1
    return delivered
