import os
import subprocess
import sys
from pathlib import Path
from unittest.mock import AsyncMock

import pytest
from aiogram.exceptions import TelegramConflictError, TelegramNetworkError
from aiogram.methods import GetUpdates

from bot.main import PollingDispatcher

ROOT = Path(__file__).resolve().parents[1]


def test_migration_on_empty_database_and_idempotent_upgrade(tmp_path):
    env = dict(
        os.environ, DATABASE_URL=f"sqlite+aiosqlite:///{tmp_path / 'migrated.db'}", BOT_TOKEN=""
    )
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
    import sqlite3

    with sqlite3.connect(tmp_path / "migrated.db") as connection:
        tables = {
            row[0]
            for row in connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'")
        }
        assert {"users", "profiles", "reactions", "matches", "blocks", "reports"} <= tables
        assert connection.execute("SELECT version_num FROM alembic_version").fetchone() == ("0002",)


def test_empty_token_startup_is_clear(tmp_path):
    result = subprocess.run(
        [sys.executable, "-m", "bot.main"],
        cwd=ROOT,
        env=dict(os.environ, BOT_TOKEN=""),
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
