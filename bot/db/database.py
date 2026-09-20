from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from bot.config import normalize_database_url


class Database:
    def __init__(self, url: str) -> None:
        self.engine = create_async_engine(
            normalize_database_url(url),
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
            pool_timeout=30,
        )
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)

    async def close(self) -> None:
        await self.engine.dispose()
