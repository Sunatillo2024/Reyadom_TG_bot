from typing import Literal
from urllib.parse import urlparse

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(value: str) -> str:
    """Return a PostgreSQL async URL, including Railway's standard URL format."""
    value = value.strip()
    if value.startswith("postgresql+asyncpg://"):
        return value
    if value.startswith("postgresql://"):
        return value.replace("postgresql://", "postgresql+asyncpg://", 1)
    if value.startswith("postgres://"):
        return value.replace("postgres://", "postgresql+asyncpg://", 1)
    raise ValueError(
        "DATABASE_URL должен быть PostgreSQL URL: "
        "postgresql+asyncpg://... или postgresql://..."
    )


def normalize_redis_url(value: str) -> str:
    """Validate a Redis URL without ever logging its credentials."""
    value = value.strip()
    parsed = urlparse(value)
    if parsed.scheme not in {"redis", "rediss"} or not parsed.hostname:
        raise ValueError("REDIS_URL должен быть URL вида redis://host:6379/0")
    return value


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr = SecretStr("")
    admin_ids: list[int] = Field(default_factory=list)
    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    fsm_state_ttl: int = Field(default=86_400, ge=1)
    fsm_data_ttl: int = Field(default=86_400, ge=1)
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    stars_sales_enabled: bool = True
    welcome_trial_enabled: bool = True
    welcome_trial_days: int = Field(default=7, ge=1, le=365)

    @field_validator("database_url")
    @classmethod
    def postgresql_async_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @field_validator("redis_url")
    @classmethod
    def redis_connection_url(cls, value: str) -> str:
        return normalize_redis_url(value)

    @field_validator("admin_ids")
    @classmethod
    def valid_ids(cls, value: list[int]) -> list[int]:
        if any(item <= 0 or item > 2**63 - 1 for item in value):
            raise ValueError(
                "ADMIN_IDS должен содержать список положительных 64-битных Telegram ID"
            )
        return value
