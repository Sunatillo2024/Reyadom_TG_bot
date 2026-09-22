from typing import Literal

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


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr = SecretStr("")
    admin_ids: list[int] = Field(default_factory=list)
    database_url: str
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    stars_sales_enabled: bool = True
    welcome_trial_enabled: bool = True
    welcome_trial_days: int = Field(default=7, ge=1, le=365)

    @field_validator("database_url")
    @classmethod
    def postgresql_async_url(cls, value: str) -> str:
        return normalize_database_url(value)

    @field_validator("admin_ids")
    @classmethod
    def valid_ids(cls, value: list[int]) -> list[int]:
        if any(item <= 0 or item > 2**63 - 1 for item in value):
            raise ValueError(
                "ADMIN_IDS должен содержать список положительных 64-битных Telegram ID"
            )
        return value
