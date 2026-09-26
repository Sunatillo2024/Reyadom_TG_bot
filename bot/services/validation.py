import re
from math import isfinite

from bot.i18n import tr

CONTACT = re.compile(
    r"@\w+|(?:https?|tg|ftp)://|(?:www\.|(?:t|telegram)\.me/)|"
    r"\b[\w-]+(?:\.[\w-]+)*\.[a-zA-Z]{2,}(?:\b|/)",
    re.IGNORECASE,
)


class RuleError(ValueError):
    pass


def clean_text(value: str, minimum: int, maximum: int) -> str:
    value = value.strip()
    if not minimum <= len(value) <= maximum:
        raise RuleError(tr("err_text_length", minimum=minimum, maximum=maximum))
    if CONTACT.search(value):
        raise RuleError(tr("err_no_contacts"))
    return value


def age_value(value: str | int) -> int:
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]{2}", str(value).strip()):
        raise RuleError(tr("err_age_invalid"))
    age = int(value)
    if not 18 <= age <= 99:
        raise RuleError(tr("err_age_invalid"))
    return age


def age_range(minimum: int, maximum: int) -> tuple[int, int]:
    low, high = age_value(minimum), age_value(maximum)
    if low > high:
        raise RuleError(tr("err_min_max"))
    return low, high


def normalize_city(value: str) -> str:
    return " ".join(value.split()).casefold()


def coordinates(latitude: float | str, longitude: float | str) -> tuple[float, float]:
    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError) as exc:
        raise RuleError(tr("err_location_failed")) from exc
    if not isfinite(lat) or not isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise RuleError(tr("err_location_failed"))
    return lat, lon
