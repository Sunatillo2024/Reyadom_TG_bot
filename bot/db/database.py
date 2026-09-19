import asyncio
from math import asin, cos, radians, sin, sqrt
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine


def distance_km(
    latitude_a: float, longitude_a: float, latitude_b: float, longitude_b: float
) -> float:
    """Return the great-circle distance between two latitude/longitude pairs."""
    lat_a, lon_a, lat_b, lon_b = map(radians, (latitude_a, longitude_a, latitude_b, longitude_b))
    haversine = sin((lat_b - lat_a) / 2) ** 2 + cos(lat_a) * cos(lat_b) * sin(
        (lon_b - lon_a) / 2
    ) ** 2
    return 6_371.0088 * 2 * asin(sqrt(haversine))


class Database:
    def __init__(self, url: str) -> None:
        path = make_url(url).database
        if path and path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.engine = create_async_engine(url, connect_args={"timeout": 10})
        event.listen(self.engine.sync_engine, "connect", self._configure_sqlite)
        self.sessions = async_sessionmaker(self.engine, expire_on_commit=False)
        # All writers use the same process-local lock, never held across Telegram calls.
        self.write_lock = asyncio.Lock()

    @staticmethod
    def _configure_sqlite(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA busy_timeout=10000")
        connection.create_function("distance_km", 4, distance_km, deterministic=True)
        cursor.close()

    async def close(self) -> None:
        await self.engine.dispose()
