from __future__ import annotations

import asyncio
import logging
import os
import time

import asyncpg

from core.error_handling import ErrorCategory, with_async_error_handling
from database.metrics import queries_total, query_errors_total
from yosai_intel_dashboard.src.services.common.secrets import get_secret

logger = logging.getLogger(__name__)


class TimescaleDBManager:
    """Async TimescaleDB manager with connection pooling."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or self._build_dsn()
        self.pool: asyncpg.Pool | None = None
        self._health_task: asyncio.Task | None = None

    # ------------------------------------------------------------------
    def _build_dsn(self) -> str:
        host = os.getenv("TIMESCALE_HOST") or get_secret("secret/data/timescale#host")
        port = os.getenv("TIMESCALE_PORT") or get_secret("secret/data/timescale#port")
        db = os.getenv("TIMESCALE_DB_NAME") or get_secret("secret/data/timescale#name")
        user = os.getenv("TIMESCALE_DB_USER") or get_secret(
            "secret/data/timescale#user"
        )
        pwd = os.getenv("TIMESCALE_DB_PASSWORD") or get_secret(
            "secret/data/timescale#password"
        )
        return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

    # ------------------------------------------------------------------
    async def connect(self, retries: int = 3, backoff: float = 0.5) -> None:
        """Initialise the connection pool with retry/backoff."""
        if self.pool is not None:
            return

        attempt = 0
        delay = backoff
        while True:
            try:
                self.pool = await asyncpg.create_pool(
                    dsn=self.dsn,
                    min_size=int(
                        os.getenv("TIMESCALE_POOL_MIN")
                        or get_secret("secret/data/timescale#pool_min")
                        or 1
                    ),
                    max_size=int(
                        os.getenv("TIMESCALE_POOL_MAX")
                        or get_secret("secret/data/timescale#pool_max")
                        or 5
                    ),
                )
                async with self.pool.acquire() as conn:
                    await self._setup(conn)
                await self.start_health_monitor()
                break
            except Exception as exc:  # pragma: no cover - runtime failures
                attempt += 1
                logger.error(
                    "Timescale connection failed (attempt %s): %s", attempt, exc
                )
                if attempt >= retries:
                    raise
                await asyncio.sleep(delay)
                delay *= 2

    # ------------------------------------------------------------------
    async def _setup(self, conn: asyncpg.Connection) -> None:
        await conn.execute("CREATE EXTENSION IF NOT EXISTS timescaledb")
        await conn.execute(
            """
            CREATE TABLE IF NOT EXISTS access_events (
                time TIMESTAMPTZ NOT NULL,
                event_id UUID PRIMARY KEY,
                person_id VARCHAR(50),
                door_id VARCHAR(50),
                facility_id VARCHAR(50),
                access_result VARCHAR(20),
                badge_status VARCHAR(20),
                response_time_ms INTEGER,
                metadata JSONB
            )
            """,
        )
        await conn.execute(
            "SELECT create_hypertable('access_events', 'time', if_not_exists => TRUE)"
        )
        await conn.execute(
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS access_events_5min
            WITH (timescaledb.continuous) AS
            SELECT time_bucket('5 minutes', time) AS bucket,
                   facility_id,
                   COUNT(*) AS event_count
            FROM access_events
            GROUP BY bucket, facility_id
            WITH NO DATA
            """,
        )
        await conn.execute(
            """
            SELECT add_continuous_aggregate_policy(
                'access_events_5min',
                start_offset => INTERVAL '1 day',
                end_offset => INTERVAL '1 minute',
                schedule_interval => INTERVAL '5 minutes',
                if_not_exists => TRUE
            )
            """,
        )
        compression_days = int(os.getenv("TIMESCALE_COMPRESSION_DAYS", "30"))
        retention_days = int(os.getenv("TIMESCALE_RETENTION_DAYS", "365"))
        await conn.execute(
            "SELECT add_compression_policy('access_events', INTERVAL $1 || ' days', if_not_exists => TRUE)",
            compression_days,
        )
        await conn.execute(
            "SELECT add_retention_policy('access_events', INTERVAL $1 || ' days', if_not_exists => TRUE)",
            retention_days,
        )

    # ------------------------------------------------------------------
    @with_async_error_handling(category=ErrorCategory.DATABASE, reraise=True)
    async def fetch(self, query: str, *args: object) -> list[asyncpg.Record]:
        if self.pool is None:
            await self.connect()
        assert self.pool is not None
        start = time.perf_counter()
        queries_total.inc()
        try:
            async with self.pool.acquire() as conn:
                result = await conn.fetch(query, *args)
        except Exception:
            query_errors_total.inc()
            elapsed_ms = (time.perf_counter() - start) * 1000
            logger.error("Query failed after %.2fms", elapsed_ms)
            raise
        else:
            elapsed_ms = (time.perf_counter() - start) * 1000
            if elapsed_ms > 1000:
                logger.warning("Slow query: %.2fms", elapsed_ms)
            return result

    # ------------------------------------------------------------------
    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    # ------------------------------------------------------------------
    @with_async_error_handling(category=ErrorCategory.DATABASE)
    async def check_integrity(self) -> None:
        """Verify hypertable and continuous aggregate integrity."""
        if self.pool is None:
            await self.connect()
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            ht_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM timescaledb_information.hypertables
                WHERE hypertable_name = 'access_events'
                """
            )
            if ht_count != 1:
                logger.error("Hypertable access_events missing (%s)", ht_count)

            agg_count = await conn.fetchval(
                """
                SELECT COUNT(*) FROM timescaledb_information.continuous_aggregates
                WHERE view_name = 'access_events_5min'
                """
            )
            if agg_count != 1:
                logger.error(
                    "Continuous aggregate access_events_5min missing (%s)", agg_count
                )

    # ------------------------------------------------------------------
    async def _health_monitor_loop(self, interval: int) -> None:
        while True:
            await self.check_integrity()
            await asyncio.sleep(interval)

    async def start_health_monitor(self, interval: int = 300) -> None:
        if self._health_task is None:
            self._health_task = asyncio.create_task(self._health_monitor_loop(interval))

    async def stop_health_monitor(self) -> None:
        if self._health_task is not None:
            self._health_task.cancel()
            try:
                await self._health_task
            except asyncio.CancelledError:
                pass
            self._health_task = None


__all__ = ["TimescaleDBManager"]
