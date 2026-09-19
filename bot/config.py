from typing import Literal

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    bot_token: SecretStr = SecretStr("")
    admin_ids: list[int] = Field(default_factory=list)
    database_url: str = "sqlite+aiosqlite:///./data/bot.db"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator("database_url")
    @classmethod
    def sqlite_only(cls, value: str) -> str:
        if not value.startswith("sqlite+aiosqlite:///"):
            raise ValueError("DATABASE_URL должен начинаться с sqlite+aiosqlite:///")
        return value

    @field_validator("admin_ids")
    @classmethod
    def valid_ids(cls, value: list[int]) -> list[int]:
        if any(item <= 0 or item > 2**63 - 1 for item in value):
            raise ValueError("ADMIN_IDS должен содержать список положительных 64-битных Telegram ID")
        return value
