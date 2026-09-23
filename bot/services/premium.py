"""Premium capabilities service."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from dateutil.relativedelta import relativedelta

from bot.db.models import User

# Timezone for daily limits reset. All users share the same reset boundary.
DAILY_LIMIT_TIMEZONE = "UTC"

# Premium plan definitions
PREMIUM_PLANS = {
    "premium_3d": {"duration_days": 3, "price_stars": 200, "label": "3 дня"},
    "premium_1m": {"duration_months": 1, "price_stars": 500, "label": "1 месяц"},
    "premium_3m": {"duration_months": 3, "price_stars": 1200, "label": "3 месяца"},
}

# Capability limits
FREE_DAILY_LIKES = 30
FREE_DAILY_UNDO = 1
PREMIUM_PHOTO_LIMIT = 5
FREE_PHOTO_LIMIT = 1
BOOST_DURATION_MINUTES = 30
BOOST_COOLDOWN_HOURS = 24

PlanCode = Literal["premium_3d", "premium_1m", "premium_3m"]


@dataclass(frozen=True)
class PremiumStatus:
    is_premium: bool
    until: datetime | None
    days_left: int
    kind: Literal["trial", "paid"] | None


def get_effective_premium_until(user: User) -> datetime | None:
    """Return the later of the welcome-trial and paid Premium end timestamps."""
    candidates = [value for value in (user.trial_ends_at, user.premium_until) if value]
    return max(candidates, default=None)


def has_premium(user: User, now: datetime | None = None) -> bool:
    """Check if user has active Premium. Single source of truth."""
    if now is None:
        now = datetime.now(UTC)
    effective_until = get_effective_premium_until(user)
    return effective_until is not None and effective_until > now


def premium_status(user: User, now: datetime | None = None) -> PremiumStatus:
    """Return Premium status with expiry details."""
    if now is None:
        now = datetime.now(UTC)
    effective_until = get_effective_premium_until(user)
    is_active = effective_until is not None and effective_until > now
    days = 0
    if is_active and effective_until:
        delta = effective_until - now
        days = max(0, delta.days)
    kind: Literal["trial", "paid"] | None = None
    if user.premium_until is not None and user.premium_until == effective_until and is_active:
        kind = "paid"
    elif user.trial_ends_at is not None and user.trial_ends_at == effective_until and is_active:
        kind = "trial"
    return PremiumStatus(
        is_premium=is_active,
        until=effective_until,
        days_left=days,
        kind=kind,
    )


def calculate_premium_end(
    current_until: datetime | None,
    plan_code: PlanCode,
    now: datetime | None = None,
    *,
    trial_until: datetime | None = None,
) -> datetime:
    """
    Calculate a paid Premium end date from max(now, paid end, trial end).

    Month means calendar month: 31 Jan + 1 month = 28/29 Feb (preserving time).
    If target day does not exist, use last day of that month.
    """
    if now is None:
        now = datetime.now(UTC)

    base = max(value for value in (now, current_until, trial_until) if value is not None)
    plan = PREMIUM_PLANS[plan_code]

    if "duration_days" in plan:
        return base + timedelta(days=plan["duration_days"])
    elif "duration_months" in plan:
        # relativedelta handles month-end correctly: 31 Jan + 1 month = 28/29 Feb
        return base + relativedelta(months=plan["duration_months"])
    else:
        raise ValueError(f"Invalid plan: {plan_code}")


def daily_limit_start(now: datetime | None = None) -> datetime:
    """Return the start of current daily limit period in UTC."""
    if now is None:
        now = datetime.now(UTC)
    return now.replace(hour=0, minute=0, second=0, microsecond=0)


def daily_limit_reset_at(now: datetime | None = None) -> datetime:
    """Return when daily limits reset next (start of next day UTC)."""
    return daily_limit_start(now) + timedelta(days=1)


def can_send_like(user: User, likes_sent_today: int) -> tuple[bool, str]:
    """Check if user can send a like. Returns (allowed, error_message)."""
    is_premium = has_premium(user)

    if is_premium:
        return True, ""

    if likes_sent_today >= FREE_DAILY_LIKES:
        reset_at = daily_limit_reset_at()
        return (
            False,
            f"Лимит {FREE_DAILY_LIKES} лайков исчерпан.\n"
            f"Следующее обновление: {reset_at.strftime('%H:%M')} UTC.\n\n"
            "💎 Premium снимает лимит лайков.",
        )

    return True, ""


def can_undo_pass(user: User, undos_today: int, now: datetime | None = None) -> tuple[bool, str]:
    """Check if user can undo a pass. Returns (allowed, error_message)."""
    is_premium = has_premium(user, now)

    if is_premium:
        return True, ""

    if undos_today >= FREE_DAILY_UNDO:
        reset_at = daily_limit_reset_at(now)
        return (
            False,
            f"Возврат анкеты доступен {FREE_DAILY_UNDO} раз в сутки.\n"
            f"Следующее обновление: {reset_at.strftime('%H:%M')} UTC.\n\n"
            "💎 Premium снимает лимит возвратов.",
        )

    return True, ""


def photo_limit(user: User) -> int:
    """Return maximum number of photos user can have."""
    return PREMIUM_PHOTO_LIMIT if has_premium(user) else FREE_PHOTO_LIMIT


def can_use_radius_filter(user: User) -> bool:
    """Check if user can set custom search radius."""
    return has_premium(user)


def can_use_incoming_list(user: User) -> bool:
    """Check if user can see incoming likes as a sorted list."""
    return has_premium(user)


def can_activate_boost(user: User) -> bool:
    """Check if user can activate Boost."""
    return has_premium(user)


def show_premium_badge(user: User) -> bool:
    """Check if Premium badge should be shown in profile."""
    return has_premium(user) and user.show_premium_badge
