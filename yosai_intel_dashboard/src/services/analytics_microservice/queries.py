"""Optimised TimescaleDB queries for analytics."""

from __future__ import annotations

from typing import Any, Dict, List

import asyncpg


async def hourly_event_counts(pool: asyncpg.Pool, days: int) -> List[Dict[str, Any]]:
    """Return hourly access event counts for the past *days* days."""
    rows = await pool.fetch(
        """
        SELECT time_bucket('1 hour', time) AS bucket,
               facility_id,
               COUNT(*) AS event_count
        FROM access_events
        WHERE time > NOW() - make_interval(days => $1)
        GROUP BY bucket, facility_id
        ORDER BY bucket
        """,
        days,
    )
    return [dict(r) for r in rows]


async def top_doors(
    pool: asyncpg.Pool, days: int, limit: int = 5
) -> List[Dict[str, Any]]:
    """Return most active doors within the timeframe."""
    rows = await pool.fetch(
        """
        SELECT door_id, COUNT(*) AS event_count
        FROM access_events
        WHERE time > NOW() - make_interval(days => $1)
        GROUP BY door_id
        ORDER BY event_count DESC
        LIMIT $2
        """,
        days,
        limit,
    )
    return [dict(r) for r in rows]


__all__ = ["hourly_event_counts", "top_doors"]
