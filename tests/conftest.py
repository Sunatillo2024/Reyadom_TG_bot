from itertools import count

import pytest

from bot.db.database import Database
from bot.db.models import Base, utcnow
from bot.services.store import Store


@pytest.fixture
async def store(tmp_path):
    db = Database(f"sqlite+aiosqlite:///{tmp_path / 'test.db'}")
    async with db.engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    yield Store(db, [900_001])
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
