from __future__ import annotations

"""Utility helpers for constructing and executing TimescaleDB queries."""

from functools import lru_cache
from typing import Any, Dict, List, Tuple

import asyncpg
from cachetools import LRUCache
from sqlalchemy import text
from sqlalchemy.sql import TextClause

from yosai_intel_dashboard.src.core.query_optimizer import monitor_query_performance

# Cache for compiled query plans
_QUERY_PLAN_CACHE: LRUCache[Tuple[Any, ...], TextClause] = LRUCache(maxsize=64)


def _get_cached_plan(key: Tuple[Any, ...]) -> TextClause | None:
    """Return cached query plan if present."""
    return _QUERY_PLAN_CACHE.get(key)


def _cache_plan(key: Tuple[Any, ...], query: TextClause) -> TextClause:
    _QUERY_PLAN_CACHE[key] = query
    return query


@lru_cache(maxsize=64)
def build_time_bucket_query(
    bucket_size: str,
    table: str = "access_events",
    metric: str = "COUNT(*)",
    time_column: str = "time",
    extra_filters: str | None = None,
) -> TextClause:
    """Return a time-bucketed aggregation query as :class:`TextClause`."""
    filters = f" AND {extra_filters}" if extra_filters else ""
    query = text(
        f"""
        SELECT time_bucket('{bucket_size}', {time_column}) AS bucket,
               {metric} AS value
        FROM {table}
        WHERE {time_column} >= $1 AND {time_column} < $2{filters}
        GROUP BY bucket
        ORDER BY bucket
        """
    )
    return query


@lru_cache(maxsize=64)
def build_sliding_window_query(
    window_seconds: int,
    step_seconds: int,
    table: str = "access_events",
    metric: str = "COUNT(*)",
    time_column: str = "time",
    extra_filters: str | None = None,
) -> TextClause:
    """Return a sliding window aggregation query."""
    window_points = max(int(window_seconds // step_seconds), 1)
    filters = f" AND {extra_filters}" if extra_filters else ""
    inner = (
        f"SELECT time_bucket('{step_seconds} seconds', {time_column}) AS bucket,"
        f"       {metric} AS count_bucket\n"
        f"FROM {table}\n"
        f"WHERE {time_column} >= $1 AND {time_column} < $2{filters}\n"
        f"GROUP BY bucket"
    )
    query = text(
        f"""
        SELECT bucket,
               SUM(count_bucket) OVER (
                   ORDER BY bucket
                   ROWS BETWEEN {window_points - 1} PRECEDING AND CURRENT ROW
               ) AS value
        FROM ({inner}) AS sub
        ORDER BY bucket
        """
    )
    return query


@monitor_query_performance()
async def fetch_time_buckets(
    pool: asyncpg.Pool,
    start: Any,
    end: Any,
    bucket_size: str = "1 hour",
    table: str = "access_events",
    metric: str = "COUNT(*)",
    time_column: str = "time",
    extra_filters: str | None = None,
) -> List[Dict[str, Any]]:
    """Execute a time-bucketed query and return the results as dictionaries."""
    key = ("bucket", bucket_size, table, metric, time_column, extra_filters)
    query = _get_cached_plan(key)
    if query is None:
        query = build_time_bucket_query(
            bucket_size, table, metric, time_column, extra_filters
        )
        _cache_plan(key, query)
    rows = await pool.fetch(str(query), start, end)
    return [dict(r) for r in rows]


@monitor_query_performance()
async def fetch_sliding_window(
    pool: asyncpg.Pool,
    start: Any,
    end: Any,
    window_seconds: int = 3600,
    step_seconds: int = 60,
    table: str = "access_events",
    metric: str = "COUNT(*)",
    time_column: str = "time",
    extra_filters: str | None = None,
) -> List[Dict[str, Any]]:
    """Execute a sliding-window aggregation and return the results."""
    key = (
        "window",
        window_seconds,
        step_seconds,
        table,
        metric,
        time_column,
        extra_filters,
    )
    query = _get_cached_plan(key)
    if query is None:
        query = build_sliding_window_query(
            window_seconds, step_seconds, table, metric, time_column, extra_filters
        )
        _cache_plan(key, query)
    rows = await pool.fetch(str(query), start, end)
    return [dict(r) for r in rows]


__all__ = [
    "build_time_bucket_query",
    "build_sliding_window_query",
    "fetch_time_buckets",
    "fetch_sliding_window",
]
