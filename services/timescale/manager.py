from __future__ import annotations

import logging
import os

import asyncpg

from services.common.secrets import get_secret

logger = logging.getLogger(__name__)


class TimescaleDBManager:
    """Async TimescaleDB manager with connection pooling."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or self._build_dsn()
        self.pool: asyncpg.Pool | None = None

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
    async def connect(self) -> None:
        """Initialise the connection pool and ensure hypertables."""
        if self.pool is None:
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
            "SELECT add_compression_policy('access_events',"
            f" INTERVAL '{compression_days} days', if_not_exists => TRUE)"
        )
        await conn.execute(
            "SELECT add_retention_policy('access_events',"
            f" INTERVAL '{retention_days} days', if_not_exists => TRUE)"
        )

    # ------------------------------------------------------------------
    async def fetch(self, query: str, *args: object) -> list[asyncpg.Record]:
        if self.pool is None:
            await self.connect()
        assert self.pool is not None
        async with self.pool.acquire() as conn:
            return await conn.fetch(query, *args)

    # ------------------------------------------------------------------
    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None


__all__ = ["TimescaleDBManager"]
