import os
from itertools import count

import pytest
from sqlalchemy.engine import make_url

from bot.db.database import Database
from bot.db.models import Base, utcnow
from bot.services.store import Store


def _test_database_url() -> str:
    url = os.environ.get("TEST_DATABASE_URL", "")
    if not url:
        pytest.skip("TEST_DATABASE_URL is required for PostgreSQL integration tests")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql" or not (parsed.database or "").endswith("_test"):
        pytest.fail("TEST_DATABASE_URL must be a PostgreSQL database ending in '_test'")
    return url


@pytest.fixture
async def store():
    db = Database(_test_database_url())
    async with db.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
    yield Store(db, [900_001])
    async with db.engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
    await db.close()


@pytest.fixture
def make_user(store):
    ids = count(100_001)

    async def create(*, confirmed=True, **changes):
        telegram_id = next(ids)
        user = await store.sync_user(telegram_id, f"user_{telegram_id}")
        draft = dict(
            name="Ali",
            age=25,
            gender="male",
            seeking="any",
            city="Toshkent",
            bio="Salom",
            photo_file_id="telegram-photo-id",
            consent_at=utcnow(),
        )
        draft.update(changes)
        if confirmed:
            await store.save_profile(user.id, draft)
        return user

    return create
