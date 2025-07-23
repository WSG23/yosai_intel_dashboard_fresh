from __future__ import annotations

import datetime as _dt
from typing import Any, Dict

import asyncpg


async def fetch_dashboard_summary(pool: asyncpg.Pool, days: int = 7) -> Dict[str, Any]:
    """Return basic dashboard summary using asyncpg."""
    end_date = _dt.datetime.now()
    start_date = end_date - _dt.timedelta(days=days)

    summary_query = """
        SELECT event_type, status, COUNT(*) AS count
        FROM access_events
        WHERE timestamp >= $1 AND timestamp <= $2
        GROUP BY event_type, status
    """

    rows = await pool.fetch(summary_query, start_date, end_date)
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


async def fetch_access_patterns(pool: asyncpg.Pool, days: int = 7) -> Dict[str, Any]:
    """Return access pattern analytics using asyncpg."""
    end_date = _dt.datetime.now()
    start_date = end_date - _dt.timedelta(days=days)

    hourly_query = """
        SELECT extract(hour FROM timestamp) AS hour, COUNT(*) AS event_count
        FROM access_events
        WHERE timestamp >= $1 AND timestamp <= $2
        GROUP BY hour
        ORDER BY hour
    """
    rows = await pool.fetch(hourly_query, start_date, end_date)
    hourly_data = [dict(r) for r in rows]
    peak_hour = max((r["hour"] for r in rows), default=None)

    return {
        "hourly_data": hourly_data,
        "peak_hour": peak_hour,
        "total_hours_analyzed": len(hourly_data),
    }
