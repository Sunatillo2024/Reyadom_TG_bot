import asyncio
import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramConflictError, TelegramNetworkError
from aiogram.methods import GetUpdates
from sqlalchemy import text
from sqlalchemy.engine import make_url

from bot.config import normalize_database_url
from bot.db.database import Database
from bot.main import PollingDispatcher
from bot.services.store import Store

ROOT = Path(__file__).resolve().parents[1]


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql" or not (parsed.database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must be a PostgreSQL database ending in '_test'")
    return url


def test_database_url_normalization_and_sqlite_rejection():
    assert normalize_database_url("postgresql://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )
    assert normalize_database_url("postgres://user:pass@host/db") == (
        "postgresql+asyncpg://user:pass@host/db"
    )
    with pytest.raises(ValueError, match="PostgreSQL"):
        normalize_database_url("sqlite+aiosqlite:///data/bot.db")


def test_migration_on_empty_database_and_idempotent_upgrade():
    database_url = _test_database_url()

    async def reset_schema() -> None:
        db = Database(database_url)
        try:
            async with db.engine.begin() as connection:
                await connection.execute(text("DROP SCHEMA public CASCADE"))
                await connection.execute(text("CREATE SCHEMA public"))
        finally:
            await db.close()

    async def insert_legacy_user() -> None:
        db = Database(database_url)
        try:
            async with db.engine.begin() as connection:
                await connection.execute(
                    text(
                        "INSERT INTO users "
                        "(telegram_id, username, is_banned, show_premium_badge, created_at) "
                        "VALUES (880001, 'legacy', false, true, NOW())"
                    )
                )
                # A second legacy user keeps an anketa so the 0011 backfill has
                # a profiles.consent_at row to copy onto the user.
                await connection.execute(
                    text(
                        "INSERT INTO users "
                        "(telegram_id, username, is_banned, show_premium_badge, created_at) "
                        "VALUES (880002, 'legacy_anketa', false, true, NOW())"
                    )
                )
                await connection.execute(
                    text(
                        "INSERT INTO profiles "
                        "(user_id, name, age, gender, seeking, city, city_normalized, "
                        "bio, photo_file_id, min_age, max_age, own_city_only, is_active, "
                        "consent_at, updated_at) "
                        "SELECT id, 'Legacy', 25, 'male', 'any', 'Toshkent', 'toshkent', "
                        "'', 'photo', 18, 99, true, true, NOW(), NOW() "
                        "FROM users WHERE telegram_id = 880002"
                    )
                )
        finally:
            await db.close()

    asyncio.run(reset_schema())
    env = dict(os.environ, DATABASE_URL=database_url, BOT_TOKEN="")
    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "0005"],
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    asyncio.run(insert_legacy_user())

    for args in (("upgrade", "head"), ("upgrade", "head"), ("check",)):
        result = subprocess.run(
            [sys.executable, "-m", "alembic", *args],
            cwd=ROOT,
            env=env,
            text=True,
            capture_output=True,
            timeout=30,
        )
        assert result.returncode == 0, result.stdout + result.stderr

    async def inspect_schema() -> None:
        db = Database(database_url)
        try:
            async with db.engine.connect() as connection:
                tables = set(
                    await connection.scalars(
                        text("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                    )
                )
                assert {"users", "profiles", "reactions", "matches", "blocks", "reports"} <= tables
                assert await connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                    "0012"
                )
                legacy = (
                    await connection.execute(
                        text(
                            "SELECT trial_used, trial_started_at, trial_ends_at "
                            "FROM users WHERE telegram_id = 880001"
                        )
                    )
                ).one()
                assert legacy == (True, None, None)
                # Migration 0011 backfills the consent flag from surviving profiles.
                consented = (
                    await connection.execute(
                        text(
                            "SELECT u.consent_at "
                            "FROM users AS u JOIN profiles AS p ON p.user_id = u.id "
                            "WHERE u.telegram_id = 880002"
                        )
                    )
                ).one()
                assert consented[0] is not None
                assert await connection.scalar(
                    text("SELECT consent_at FROM users WHERE telegram_id = 880001")
                ) is None
                legacy_store = Store(db, [], welcome_trial_enabled=True, welcome_trial_days=7)
                synced = await legacy_store.sync_user_with_status(880_001, "legacy")
                assert not synced.welcome_trial_granted
                assert synced.user.trial_ends_at is None
        finally:
            await db.close()

    asyncio.run(inspect_schema())


def test_empty_token_startup_is_clear():
    database_url = os.environ.get(
        "TEST_DATABASE_URL", "postgresql+asyncpg://postgres:password@localhost/ryadom_bot_test"
    )
    result = subprocess.run(
        [sys.executable, "-m", "bot.main"],
        cwd=ROOT,
        env=dict(os.environ, BOT_TOKEN="", DATABASE_URL=database_url),
        text=True,
        capture_output=True,
        timeout=15,
    )
    assert result.returncode == 2
    assert "BOT_TOKEN пуст" in result.stderr
    assert "Traceback" not in result.stderr


async def test_polling_conflict_exits_and_network_retries_are_bounded(monkeypatch):
    request = GetUpdates()
    bot = AsyncMock(side_effect=TelegramConflictError(method=request, message="conflict"))
    with pytest.raises(TelegramConflictError):
        await anext(PollingDispatcher._listen_updates(bot))
    assert bot.await_count == 1
    sleep = AsyncMock()
    monkeypatch.setattr("bot.main.asyncio.sleep", sleep)
    bot = AsyncMock(side_effect=TelegramNetworkError(method=request, message="offline"))
    with pytest.raises(TelegramNetworkError):
        await anext(PollingDispatcher._listen_updates(bot))
    assert bot.await_count == 5
    assert sleep.await_count == 4
