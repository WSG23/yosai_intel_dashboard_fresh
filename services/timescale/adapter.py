from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Iterable, List

import asyncpg
from prometheus_client import Counter, Histogram

from services.common.secrets import get_secret
from core.query_optimizer import monitor_query_performance

from .models import AccessEvent

logger = logging.getLogger(__name__)

# Prometheus metrics -----------------------------------------------------------
connection_failures = Counter(
    "timescale_connection_failures_total",
    "Total Timescale connection failures",
)
query_latency = Histogram(
    "timescale_query_latency_seconds",
    "Latency of Timescale queries",
)


class TimescaleAdapter:
    """Async TimescaleDB adapter with connection pooling and failover."""

    def __init__(self, dsn: str | None = None) -> None:
        self.dsn = dsn or self._build_dsn()
        self.fallback_dsn = self._build_dsn(fallback=True)
        self.pool: asyncpg.Pool | None = None

    # ------------------------------------------------------------------
    def _build_dsn(self, *, fallback: bool = False) -> str:
        prefix = "TIMESCALE_FALLBACK_" if fallback else "TIMESCALE_"
        host = os.getenv(f"{prefix}HOST") or get_secret(
            f"secret/data/timescale#{'fallback_host' if fallback else 'host'}"
        )
        port = os.getenv(f"{prefix}PORT") or get_secret(
            f"secret/data/timescale#{'fallback_port' if fallback else 'port'}"
        )
        db = os.getenv(f"{prefix}DB_NAME") or get_secret(
            f"secret/data/timescale#{'fallback_name' if fallback else 'name'}"
        )
        user = os.getenv(f"{prefix}DB_USER") or get_secret(
            f"secret/data/timescale#{'fallback_user' if fallback else 'user'}"
        )
        pwd = os.getenv(f"{prefix}DB_PASSWORD") or get_secret(
            f"secret/data/timescale#{'fallback_password' if fallback else 'password'}"
        )
        return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"

    # ------------------------------------------------------------------
    async def connect(self) -> None:
        """Initialise the connection pool with optional failover."""
        if self.pool is not None:
            return
        try:
            self.pool = await asyncpg.create_pool(dsn=self.dsn)
        except Exception as exc:  # pragma: no cover - network failures
            connection_failures.inc()
            logger.warning("Timescale connection failed: %s", exc)
            if self.fallback_dsn:
                logger.info("Retrying with fallback DSN")
                self.pool = await asyncpg.create_pool(dsn=self.fallback_dsn)
            else:
                raise
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
            ALTER TABLE access_events SET (
                timescaledb.compress,
                timescaledb.compress_orderby = 'time DESC',
                timescaledb.compress_segmentby = 'facility_id'
            )
            """,
        )
        await conn.execute(
            "SELECT add_compression_policy('access_events', INTERVAL '7 days', if_not_exists => TRUE)"
        )
        await conn.execute(
            "SELECT add_retention_policy('access_events', INTERVAL '90 days', if_not_exists => TRUE)"
        )

    # ------------------------------------------------------------------
    async def close(self) -> None:
        if self.pool is not None:
            await self.pool.close()
            self.pool = None

    # ------------------------------------------------------------------
    async def _execute(self, query: str, *args: object) -> list[asyncpg.Record]:
        if self.pool is None:
            await self.connect()
        assert self.pool is not None
        start = datetime.now()
        async with self.pool.acquire() as conn:
            result = await conn.fetch(query, *args)
        query_latency.observe((datetime.now() - start).total_seconds())
        return result

    # ------------------------------------------------------------------
    async def bulk_insert(self, events: Iterable[AccessEvent]) -> None:
        """Insert ``events`` efficiently using ``COPY``."""
        events_list = list(events)
        if not events_list:
            return
        if self.pool is None:
            await self.connect()
        assert self.pool is not None
        records = [
            (
                e.time,
                e.event_id,
                e.person_id,
                e.door_id,
                e.facility_id,
                e.access_result,
                e.badge_status,
                e.response_time_ms,
                json.dumps(e.metadata) if isinstance(e.metadata, dict) else e.metadata,
            )
            for e in events_list
        ]
        cols = [
            "time",
            "event_id",
            "person_id",
            "door_id",
            "facility_id",
            "access_result",
            "badge_status",
            "response_time_ms",
            "metadata",
        ]
        async with self.pool.acquire() as conn:
            await conn.copy_records_to_table("access_events", records=records, columns=cols)

    # ------------------------------------------------------------------
    @monitor_query_performance()
    async def hourly_event_counts(self, hours: int = 24) -> list[asyncpg.Record]:
        """Return counts grouped by hour for the last ``hours`` hours."""
        start_time = datetime.utcnow() - timedelta(hours=hours)
        query = (
            "SELECT time_bucket('1 hour', time) AS bucket, COUNT(*) AS event_count "
            "FROM access_events WHERE time >= $1 GROUP BY bucket ORDER BY bucket"
        )
        return await self._execute(query, start_time)


__all__ = [
    "TimescaleAdapter",
    "connection_failures",
    "query_latency",
]
