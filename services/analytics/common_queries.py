from __future__ import annotations

"""Shared asyncpg-based query implementations for analytics."""

import asyncio
import datetime as _dt
import time
from typing import Any, Dict, Protocol

import asyncpg

from database.metrics import queries_total, query_errors_total


# a lightweight protocol so both Pool and Connection can be used
class _Fetcher(Protocol):
    async def fetch(self, query: str, *args: Any) -> list[asyncpg.Record]: ...


async def fetch_dashboard_summary(conn: _Fetcher, days: int = 7) -> Dict[str, Any]:
    """Return basic dashboard summary using an asyncpg connection."""
    end_date = _dt.datetime.now()
    start_date = end_date - _dt.timedelta(days=days)

    summary_query = """
        SELECT event_type, status, COUNT(*) AS count
        FROM access_events
        WHERE timestamp >= $1 AND timestamp <= $2
        GROUP BY event_type, status
    """

    start = time.perf_counter()
    queries_total.inc()
    try:
        rows = await conn.fetch(summary_query, start_date, end_date)
    except Exception:
        query_errors_total.inc()
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > 1000:
            import logging

            logging.getLogger(__name__).warning("Slow query: %.2fms", elapsed_ms)
    total_events = sum(r["count"] for r in rows) if rows else 0
    success_events = sum(r["count"] for r in rows if r["status"] == "success")
    success_rate = (
        round((success_events / total_events) * 100, 2) if total_events else 0
    )
    breakdown = [dict(r) for r in rows]

    return {
        "status": "success",
        "summary": {
            "total_events": total_events,
            "success_rate": success_rate,
            "event_breakdown": breakdown,
            "period_days": days,
        },
    }


async def fetch_access_patterns(
    conn: _Fetcher,
    days: int = 7,
    *,
    limit: int | None = None,
    offset: int | None = None,
) -> Dict[str, Any]:
    """Return access pattern analytics using an asyncpg connection.

    Parameters
    ----------
    conn:
        Connection or pool used to execute the query.
    days:
        Number of days back to include in the analysis.
    limit:
        Maximum number of rows to return.
    offset:
        Row offset for pagination.
    """
    end_date = _dt.datetime.now()
    start_date = end_date - _dt.timedelta(days=days)

    hourly_query = """
        SELECT extract(hour FROM timestamp) AS hour, COUNT(*) AS event_count
        FROM access_events
        WHERE timestamp >= $1 AND timestamp <= $2
        GROUP BY hour
        ORDER BY hour
    """
    count_query = f"SELECT COUNT(*) FROM ({hourly_query}) AS sub"

    query = hourly_query
    params = [start_date, end_date]
    if limit is not None:
        query += f" LIMIT ${len(params) + 1}"
        params.append(limit)
    if offset is not None:
        query += f" OFFSET ${len(params) + 1}"
        params.append(offset)

    start = time.perf_counter()
    queries_total.inc()
    try:
        rows, total = await asyncio.gather(
            conn.fetch(query, *params),
            conn.fetchval(count_query, start_date, end_date),
        )
    except Exception:
        query_errors_total.inc()
        raise
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if elapsed_ms > 1000:
            import logging

            logging.getLogger(__name__).warning("Slow query: %.2fms", elapsed_ms)

    hourly_data = [dict(r) for r in rows]
    peak_hour = max((r["hour"] for r in rows), default=None)

    return {
        "hourly_data": hourly_data,
        "peak_hour": peak_hour,
        "total_count": int(total),
    }


__all__ = ["fetch_dashboard_summary", "fetch_access_patterns"]
