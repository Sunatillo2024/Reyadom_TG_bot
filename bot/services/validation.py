import re
from math import isfinite

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
        raise RuleError(f"Текст должен содержать {minimum}–{maximum} символов.")
    if CONTACT.search(value):
        raise RuleError("Не указывай контакты, @username и ссылки.")
    return value


def age_value(value: str | int) -> int:
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]{2}", str(value).strip()):
        raise RuleError("Возраст должен быть от 18 до 99 лет. Попробуй ещё раз 💜")
    age = int(value)
    if not 18 <= age <= 99:
        raise RuleError("Возраст должен быть от 18 до 99 лет. Попробуй ещё раз 💜")
    return age


def age_range(minimum: int, maximum: int) -> tuple[int, int]:
    low, high = age_value(minimum), age_value(maximum)
    if low > high:
        raise RuleError("Минимальный возраст не должен быть больше максимального.")
    return low, high


def normalize_city(value: str) -> str:
    return " ".join(value.split()).casefold()


def coordinates(latitude: float | str, longitude: float | str) -> tuple[float, float]:
    try:
        lat, lon = float(latitude), float(longitude)
    except (TypeError, ValueError) as exc:
        raise RuleError("Не получилось определить геолокацию. Попробуй ещё раз.") from exc
    if not isfinite(lat) or not isfinite(lon) or not -90 <= lat <= 90 or not -180 <= lon <= 180:
        raise RuleError("Не получилось определить геолокацию. Попробуй ещё раз.")
    return lat, lon
