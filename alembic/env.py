import asyncio

from alembic import context
from bot.config import Settings
from bot.db.database import Database
from bot.db.models import Base

target_metadata = Base.metadata


def database_url() -> str:
    """Prefer an explicit Alembic URL, otherwise load DATABASE_URL from the environment."""
    configured_url = (context.config.get_main_option("sqlalchemy.url") or "").strip()
    if configured_url:
        return Settings(database_url=configured_url).database_url
    return Settings().database_url  # type: ignore[call-arg]


def offline() -> None:
    context.configure(
        url=database_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def migrate(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def online() -> None:
    db = Database(database_url())
    try:
        async with db.engine.connect() as connection:
            await connection.run_sync(migrate)
    finally:
        await db.close()


if context.is_offline_mode():
    offline()
else:
    asyncio.run(online())
