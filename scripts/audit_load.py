"""Isolated synthetic load runner for the pre-production audit.

This script never calls Telegram. It refuses to run unless both an explicit isolation
flag and a PostgreSQL database ending in ``_test`` are supplied.
"""

import argparse
import asyncio
import json
import math
import os
import time
from collections import Counter
from datetime import UTC, datetime, timedelta
from random import Random
from statistics import median
from typing import Any

import asyncpg
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine import make_url

from bot.db.database import Database
from bot.db.models import Base
from bot.services.store import Store

MAX_VUS = 500
SEED = 20_260_923


def audit_urls() -> tuple[str, str]:
    database_url = os.environ.get("AUDIT_DATABASE_URL", "")
    redis_url = os.environ.get("AUDIT_REDIS_URL", "")
    parsed = make_url(database_url)
    if os.environ.get("AUDIT_ISOLATED") != "1":
        raise SystemExit("AUDIT_ISOLATED=1 is required")
    if parsed.get_backend_name() != "postgresql" or not (parsed.database or "").endswith("_test"):
        raise SystemExit("AUDIT_DATABASE_URL must be a PostgreSQL database ending in _test")
    if parsed.host not in {"postgres", "localhost", "127.0.0.1"}:
        raise SystemExit("AUDIT_DATABASE_URL must point to the isolated local audit service")
    if not redis_url.startswith(("redis://redis:", "redis://localhost:", "redis://127.0.0.1:")):
        raise SystemExit("AUDIT_REDIS_URL must point to the isolated local audit service")
    return database_url, redis_url


def asyncpg_dsn(database_url: str) -> str:
    return database_url.replace("postgresql+asyncpg://", "postgresql://", 1)


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def emit(payload: dict[str, Any]) -> None:
    print("AUDIT_RESULT " + json.dumps(payload, sort_keys=True), flush=True)


async def reset_and_seed(database_url: str, user_count: int) -> dict[str, Any]:
    if user_count < 1_000 or user_count > 50_000:
        raise ValueError("user_count must be between 1,000 and 50,000")
    started = time.perf_counter()
    database = Database(database_url)
    try:
        async with database.engine.begin() as connection:
            await connection.run_sync(Base.metadata.drop_all)
            await connection.run_sync(Base.metadata.create_all)
    finally:
        await database.close()

    now = datetime.now(UTC)
    premium_until = now + timedelta(days=365)
    rng = Random(SEED + user_count)
    connection = await asyncpg.connect(asyncpg_dsn(database_url))
    try:
        users = [
            (
                user_id,
                10_000_000 + user_id,
                f"audit_user_{user_id}",
                False,
                premium_until,
                True,
                True,
                now,
            )
            for user_id in range(1, user_count + 1)
        ]
        profiles = []
        photos = []
        for user_id in range(1, user_count + 1):
            latitude = 41.0 + (user_id % 1_000) * 0.0001
            longitude = 69.0 + ((user_id * 37) % 1_000) * 0.0001
            profiles.append(
                (
                    user_id,
                    f"Audit {user_id}",
                    18 + user_id % 62,
                    "male" if user_id % 2 else "female",
                    "any",
                    "Geolocation",
                    "geolocation",
                    latitude,
                    longitude,
                    "Synthetic audit profile",
                    f"audit-photo-{user_id}",
                    18,
                    99,
                    False,
                    None,
                    True,
                    now,
                    now,
                )
            )
            photos.append((user_id, f"audit-photo-{user_id}", True, 0, now))

        await connection.copy_records_to_table(
            "users",
            records=users,
            columns=(
                "id",
                "telegram_id",
                "username",
                "is_banned",
                "premium_until",
                "trial_used",
                "show_premium_badge",
                "created_at",
            ),
        )
        await connection.copy_records_to_table(
            "profiles",
            records=profiles,
            columns=(
                "user_id",
                "name",
                "age",
                "gender",
                "seeking",
                "city",
                "city_normalized",
                "latitude",
                "longitude",
                "bio",
                "photo_file_id",
                "min_age",
                "max_age",
                "own_city_only",
                "premium_radius_km",
                "is_active",
                "consent_at",
                "updated_at",
            ),
        )
        await connection.copy_records_to_table(
            "profile_photos",
            records=photos,
            columns=("user_id", "file_id", "is_primary", "position", "created_at"),
        )
        await connection.execute(
            "SELECT setval(pg_get_serial_sequence('users', 'id'), $1)", user_count
        )

        # Keep the first MAX_VUS actors and the final target pool free of seeded
        # decisions so measured writes exercise successful application flows.
        available_users = user_count - MAX_VUS
        target_pool = min(20_000, max(100, available_users // 2))
        relation_end = user_count - target_pool + 1
        relation_ids = list(range(MAX_VUS + 1, relation_end))
        rng.shuffle(relation_ids)
        pair_count = min(len(relation_ids) // 2, user_count // 20)
        reactions: list[tuple[int, int, str, datetime]] = []
        matches: list[tuple[int, int, datetime]] = []
        for index in range(pair_count):
            left, right = sorted((relation_ids[index * 2], relation_ids[index * 2 + 1]))
            reactions.extend(((left, right, "like", now), (right, left, "like", now)))
            matches.append((left, right, now))
        block_count = min(len(relation_ids) // 4, user_count // 100)
        blocks = [
            (relation_ids[index * 2], relation_ids[index * 2 + 1], now)
            for index in range(block_count)
        ]
        if reactions:
            await connection.copy_records_to_table(
                "reactions",
                records=reactions,
                columns=("from_user_id", "to_user_id", "kind", "created_at"),
            )
        if matches:
            await connection.copy_records_to_table(
                "matches",
                records=matches,
                columns=("user_low_id", "user_high_id", "created_at"),
            )
        if blocks:
            await connection.copy_records_to_table(
                "blocks",
                records=blocks,
                columns=("blocker_id", "blocked_id", "created_at"),
            )

        payment_count = min(500, user_count // 100)
        orders = []
        payments = []
        for index in range(payment_count):
            user_id = MAX_VUS + 1 + index
            order_id = f"{index + 1:032x}"
            charge_id = f"audit-charge-{index + 1}"
            orders.append(
                (
                    order_id,
                    user_id,
                    10_000_000 + user_id,
                    "premium_1m",
                    500,
                    "XTR",
                    1,
                    "months",
                    "completed",
                    now,
                    now + timedelta(hours=1),
                    now,
                    now,
                )
            )
            payments.append(
                (
                    order_id,
                    user_id,
                    10_000_000 + user_id,
                    charge_id,
                    f"premium_order:{order_id}",
                    "XTR",
                    500,
                    "completed",
                    now,
                    now,
                )
            )
        if orders:
            await connection.copy_records_to_table(
                "premium_orders",
                records=orders,
                columns=(
                    "id",
                    "user_id",
                    "buyer_telegram_id",
                    "plan_code",
                    "price_stars",
                    "currency",
                    "duration_value",
                    "duration_unit",
                    "status",
                    "terms_accepted_at",
                    "expires_at",
                    "created_at",
                    "updated_at",
                ),
            )
            await connection.copy_records_to_table(
                "premium_payments",
                records=payments,
                columns=(
                    "order_id",
                    "user_id",
                    "buyer_telegram_id",
                    "telegram_payment_charge_id",
                    "invoice_payload",
                    "currency",
                    "amount",
                    "status",
                    "paid_at",
                    "created_at",
                ),
            )
        await connection.execute("ANALYZE")
        size_bytes = await connection.fetchval("SELECT pg_database_size(current_database())")
    finally:
        await connection.close()
    result = {
        "kind": "seed",
        "users": user_count,
        "reactions": len(reactions),
        "matches": len(matches),
        "blocks": len(blocks),
        "payments": payment_count,
        "database_mb": round(size_bytes / 1024 / 1024, 2),
        "seconds": round(time.perf_counter() - started, 3),
    }
    emit(result)
    return result


async def event_loop_lag(stop: asyncio.Event, samples: list[float]) -> None:
    interval = 0.05
    expected = time.perf_counter() + interval
    while not stop.is_set():
        await asyncio.sleep(interval)
        current = time.perf_counter()
        samples.append(max(0.0, current - expected) * 1_000)
        expected = current + interval


async def run_load(
    database_url: str,
    *,
    user_count: int,
    vus: int,
    duration: float,
    label: str,
) -> dict[str, Any]:
    database = Database(database_url)
    store = Store(database, [10_000_001], welcome_trial_enabled=False)
    latencies: list[float] = []
    errors: Counter[str] = Counter()
    operations: Counter[str] = Counter()
    lag_samples: list[float] = []
    stop = asyncio.Event()
    deadline = time.perf_counter() + duration
    available_users = user_count - MAX_VUS
    target_pool = min(20_000, max(100, available_users // 2))

    async def virtual_user(worker: int) -> None:
        actor = worker + 1
        telegram_id = 10_000_000 + actor
        iteration = 0
        decision = 0
        while time.perf_counter() < deadline:
            slot = iteration % 20
            started = time.perf_counter()
            operation = "sync"
            try:
                async with asyncio.timeout(15):
                    await store.sync_user(telegram_id, f"audit_user_{actor}")
                    if 4 <= slot <= 8:
                        operation = "browse"
                        await store.next_profile(actor)
                    elif 9 <= slot <= 12:
                        operation = "pass"
                        target = user_count - ((worker * 10_007 + decision) % target_pool)
                        decision += 1
                        await store.decide(actor, target, "pass")
                    elif 13 <= slot <= 15:
                        operation = "like"
                        target = user_count - ((worker * 10_007 + decision) % target_pool)
                        decision += 1
                        await store.decide(actor, target, "like")
                    elif slot == 16:
                        operation = "profile"
                        await store.profile(actor)
                    elif slot == 17:
                        operation = "edit"
                        await store.edit_profile(actor, "bio", f"Synthetic load {iteration % 100}")
                    elif slot == 18:
                        operation = "premium"
                        await store.premium_status_info(telegram_id)
                    elif slot == 19:
                        operation = "matches"
                        await store.match_page(actor, 0)
            except Exception as exc:
                errors[type(exc).__name__] += 1
            finally:
                operations[operation] += 1
                latencies.append((time.perf_counter() - started) * 1_000)
            iteration += 1

    monitor = asyncio.create_task(event_loop_lag(stop, lag_samples))
    started = time.perf_counter()
    try:
        await asyncio.gather(*(virtual_user(worker) for worker in range(vus)))
    finally:
        stop.set()
        await monitor
        await database.close()
    elapsed = time.perf_counter() - started
    total = len(latencies)
    error_count = sum(errors.values())
    result = {
        "kind": "load",
        "label": label,
        "users": user_count,
        "vus": vus,
        "duration_s": round(elapsed, 3),
        "requests": total,
        "rps": round(total / elapsed, 2),
        "p50_ms": round(median(latencies), 2) if latencies else 0.0,
        "p95_ms": round(percentile(latencies, 0.95), 2),
        "p99_ms": round(percentile(latencies, 0.99), 2),
        "errors": error_count,
        "error_pct": round(error_count * 100 / total, 3) if total else 100.0,
        "error_types": dict(errors),
        "operations": dict(operations),
        "loop_lag_p95_ms": round(percentile(lag_samples, 0.95), 2),
        "loop_lag_max_ms": round(max(lag_samples, default=0.0), 2),
    }
    emit(result)
    return result


async def redis_latency(redis_url: str, samples: int = 1_000) -> dict[str, Any]:
    client = Redis.from_url(redis_url)
    timings = []
    try:
        for _ in range(samples):
            started = time.perf_counter()
            await client.ping()
            timings.append((time.perf_counter() - started) * 1_000)
    finally:
        await client.aclose()
    result = {
        "kind": "redis",
        "samples": samples,
        "p50_ms": round(median(timings), 3),
        "p95_ms": round(percentile(timings, 0.95), 3),
        "p99_ms": round(percentile(timings, 0.99), 3),
    }
    emit(result)
    return result


async def explain_discovery(database_url: str) -> dict[str, Any]:
    database = Database(database_url)
    store = Store(database, [], welcome_trial_enabled=False)
    statement = store._candidates(1).limit(1)
    compiled = statement.compile(
        dialect=postgresql.dialect(), compile_kwargs={"literal_binds": True}
    )
    try:
        async with database.engine.connect() as connection:
            plan = await connection.scalar(
                text("EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) " + str(compiled))
            )
            active_connections = await connection.scalar(
                text(
                    "SELECT count(*) FROM pg_stat_activity "
                    "WHERE datname = current_database() AND state = 'active'"
                )
            )
    finally:
        await database.close()
    root = plan[0]
    top = root["Plan"]
    result = {
        "kind": "explain",
        "execution_ms": round(root["Execution Time"], 3),
        "planning_ms": round(root["Planning Time"], 3),
        "top_node": top["Node Type"],
        "rows": top["Actual Rows"],
        "shared_hit_blocks": top.get("Shared Hit Blocks", 0),
        "shared_read_blocks": top.get("Shared Read Blocks", 0),
        "active_connections": active_connections,
    }
    emit(result)
    return result


async def run_matrix(database_url: str, redis_url: str, args: argparse.Namespace) -> None:
    for count in (1_000, 10_000):
        await reset_and_seed(database_url, count)
        await run_load(
            database_url,
            user_count=count,
            vus=5,
            duration=args.dataset_duration,
            label=f"dataset-{count}",
        )

    user_count = 50_000
    await reset_and_seed(database_url, user_count)
    await explain_discovery(database_url)
    await redis_latency(redis_url)

    last_stable = 1
    first_unstable: int | None = None
    for vus in (1, 10, 25, 50, 100, 200, 500):
        result = await run_load(
            database_url,
            user_count=user_count,
            vus=vus,
            duration=args.stage_duration,
            label="load",
        )
        stable = result["error_pct"] < 1 and result["p95_ms"] < 1_000
        if not stable:
            first_unstable = vus
            break
        last_stable = vus

    spike_vus = first_unstable or min(500, max(10, last_stable * 2))
    await run_load(
        database_url,
        user_count=user_count,
        vus=spike_vus,
        duration=args.spike_duration,
        label="spike",
    )
    await run_load(
        database_url,
        user_count=user_count,
        vus=1,
        duration=5,
        label="recovery",
    )
    soak_vus = max(1, math.floor(last_stable * 0.4))
    await run_load(
        database_url,
        user_count=user_count,
        vus=soak_vus,
        duration=args.soak_duration,
        label="soak",
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    matrix = subparsers.add_parser("matrix")
    matrix.add_argument("--dataset-duration", type=float, default=10)
    matrix.add_argument("--stage-duration", type=float, default=15)
    matrix.add_argument("--spike-duration", type=float, default=10)
    matrix.add_argument("--soak-duration", type=float, default=1_200)
    seed = subparsers.add_parser("seed")
    seed.add_argument("--users", type=int, required=True)
    load = subparsers.add_parser("load")
    load.add_argument("--users", type=int, required=True)
    load.add_argument("--vus", type=int, required=True)
    load.add_argument("--duration", type=float, required=True)
    load.add_argument("--label", default="manual")
    return parser.parse_args()


async def main() -> None:
    database_url, redis_url = audit_urls()
    args = parse_args()
    if args.command == "matrix":
        await run_matrix(database_url, redis_url, args)
    elif args.command == "seed":
        await reset_and_seed(database_url, args.users)
    elif args.command == "load":
        if not 1 <= args.vus <= MAX_VUS:
            raise SystemExit(f"vus must be between 1 and {MAX_VUS}")
        await run_load(
            database_url,
            user_count=args.users,
            vus=args.vus,
            duration=args.duration,
            label=args.label,
        )


if __name__ == "__main__":
    asyncio.run(main())
