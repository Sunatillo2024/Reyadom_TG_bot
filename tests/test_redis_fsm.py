import asyncio
import logging
import os
from types import SimpleNamespace
from uuid import uuid4

import pytest
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.base import DefaultKeyBuilder, StorageKey
from aiogram.fsm.storage.redis import RedisStorage
from redis.asyncio import Redis
from redis.exceptions import ConnectionError as RedisConnectionError
from redis.exceptions import RedisError

from bot.config import Settings
from bot.main import create_redis_storage, verify_redis_connection
from bot.states import Registration


@pytest.fixture
async def redis_test_resource():
    """Use isolated, prefixed keys so a test never clears application Redis data."""
    url = os.environ.get("TEST_REDIS_URL", "redis://localhost:6379/15")
    client = Redis.from_url(url)
    try:
        await client.ping()
    except RedisError:
        await client.aclose()
        pytest.skip("Redis test server is unavailable; start it with docker compose up -d redis")

    key_builder = DefaultKeyBuilder(prefix=f"test:fsm:{uuid4().hex}", with_bot_id=True)
    try:
        yield url, key_builder
    finally:
        keys = [key async for key in client.scan_iter(match=f"{key_builder.prefix}:*")]
        if keys:
            await client.delete(*keys)
        await client.aclose()


async def test_redis_connection_and_fsm_data_survive_storage_recreation(redis_test_resource):
    url, key_builder = redis_test_resource
    key_one = StorageKey(bot_id=1, chat_id=101, user_id=101)
    key_two = StorageKey(bot_id=1, chat_id=202, user_id=202)
    storage = RedisStorage.from_url(url, key_builder=key_builder, state_ttl=60, data_ttl=60)
    try:
        assert await storage.redis.ping()
        first_context = FSMContext(storage=storage, key=key_one)
        second_context = FSMContext(storage=storage, key=key_two)

        await first_context.set_state(Registration.age)
        await first_context.update_data(name="Ali", consent_at="2026-09-22T12:00:00+00:00")
        await second_context.set_state(Registration.bio)
        await second_context.update_data(name="Malika")

        assert await first_context.get_state() == Registration.age.state
        assert await first_context.get_data() == {
            "name": "Ali",
            "consent_at": "2026-09-22T12:00:00+00:00",
        }
        assert await second_context.get_state() == Registration.bio.state
        assert await second_context.get_data() == {"name": "Malika"}
    finally:
        await storage.close()

    # A new RedisStorage represents a restarted bot process using the same keys.
    resumed_storage = RedisStorage.from_url(url, key_builder=key_builder, state_ttl=60, data_ttl=60)
    try:
        resumed_context = FSMContext(storage=resumed_storage, key=key_one)
        assert await resumed_context.get_state() == Registration.age.state
        assert (await resumed_context.get_data())["name"] == "Ali"
    finally:
        await resumed_storage.close()


async def test_application_redis_storage_uses_the_configured_connection(redis_test_resource):
    url, _ = redis_test_resource
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://postgres:password@localhost/ryadom_bot",
        redis_url=url,
        fsm_state_ttl=60,
        fsm_data_ttl=60,
    )
    storage = create_redis_storage(settings)
    try:
        assert await verify_redis_connection(storage)
        key = StorageKey(bot_id=9, chat_id=9, user_id=9)
        assert storage.key_builder.build(key, "state") == "fsm:9:9:9:state"
    finally:
        await storage.close()


async def test_redis_fsm_clear_and_ttl_remove_only_temporary_keys(redis_test_resource):
    url, key_builder = redis_test_resource
    key = StorageKey(bot_id=1, chat_id=303, user_id=303)
    storage = RedisStorage.from_url(url, key_builder=key_builder, state_ttl=1, data_ttl=1)
    context = FSMContext(storage=storage, key=key)
    try:
        await context.set_state(Registration.name)
        await context.set_data({"name": "TTL user"})
        state_key = key_builder.build(key, "state")
        data_key = key_builder.build(key, "data")
        assert 0 <= await storage.redis.ttl(state_key) <= 1
        assert 0 <= await storage.redis.ttl(data_key) <= 1

        await context.clear()
        assert await context.get_state() is None
        assert await context.get_data() == {}
        assert await storage.redis.exists(state_key, data_key) == 0

        await context.set_state(Registration.name)
        await context.set_data({"name": "Expiring user"})
        await asyncio.sleep(1.2)
        assert await context.get_state() is None
        assert await context.get_data() == {}
    finally:
        await storage.close()


def test_redis_settings_have_safe_local_defaults_and_integer_ttls(monkeypatch):
    monkeypatch.delenv("REDIS_URL", raising=False)
    monkeypatch.delenv("FSM_STATE_TTL", raising=False)
    monkeypatch.delenv("FSM_DATA_TTL", raising=False)
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://postgres:password@localhost/ryadom_bot",
        fsm_state_ttl="120",
        fsm_data_ttl="240",
    )

    assert settings.redis_url == "redis://localhost:6379/0"
    assert settings.fsm_state_ttl == 120
    assert settings.fsm_data_ttl == 240


async def test_unavailable_redis_is_logged_without_connection_secret(caplog):
    storage = SimpleNamespace(
        redis=SimpleNamespace(
            ping=lambda: (_ for _ in ()).throw(
                RedisConnectionError("redis://:not-for-logs@localhost:6379/0 unavailable")
            )
        )
    )

    with caplog.at_level(logging.ERROR, logger="bot.main"):
        assert not await verify_redis_connection(storage)  # type: ignore[arg-type]

    assert "Redis ulanib bo'lmadi" in caplog.text
    assert "not-for-logs" not in caplog.text
