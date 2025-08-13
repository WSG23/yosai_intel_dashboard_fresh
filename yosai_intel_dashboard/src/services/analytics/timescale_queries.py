from __future__ import annotations

"""Utility helpers for constructing and executing TimescaleDB queries."""

import logging
from functools import lru_cache
from typing import Any, Dict, List, Tuple

import asyncpg
from cachetools import LRUCache
from sqlalchemy import text
from sqlalchemy.sql import TextClause

from yosai_intel_dashboard.src.infrastructure.security.query_builder import SecureQueryBuilder
from yosai_intel_dashboard.src.core.query_optimizer import monitor_query_performance

LOG = logging.getLogger(__name__)

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
    extra_filters: Tuple[str, ...] | None = None,
) -> TextClause:
    """Return a time-bucketed aggregation query as :class:`TextClause`.

    ``bucket_size`` and ``extra_filters`` are converted into parameter placeholders
    so the resulting query plan can be safely cached and reused for different
    values.
    """
    allowed_columns = {time_column}
    if extra_filters:
        allowed_columns.update(extra_filters)
    builder = SecureQueryBuilder(
        allowed_tables={table}, allowed_columns=allowed_columns
    )
    table_q = builder.table(table)
    time_col = builder.column(time_column)
    filters = ""
    if extra_filters:
        for i, col in enumerate(extra_filters, start=4):
            col_q = builder.column(col)
            filters += f" AND {col_q} = ${i}"
    query_str = f"""
        SELECT time_bucket($3, {time_col}) AS bucket,
               {metric} AS value
        FROM {table_q}
        WHERE {time_col} >= $1 AND {time_col} < $2{filters}
        GROUP BY bucket
        ORDER BY bucket
        """
    sql, _ = builder.build(query_str, logger=LOG)
    return text(sql)


@lru_cache(maxsize=64)
def build_sliding_window_query(
    window_seconds: int,
    step_seconds: int,
    table: str = "access_events",
    metric: str = "COUNT(*)",
    time_column: str = "time",
    extra_filters: Tuple[str, ...] | None = None,
) -> TextClause:
    """Return a sliding window aggregation query."""
    allowed_columns = {time_column}
    if extra_filters:
        allowed_columns.update(extra_filters)
    builder = SecureQueryBuilder(
        allowed_tables={table}, allowed_columns=allowed_columns
    )
    table_q = builder.table(table)
    time_col = builder.column(time_column)
    window_points = max(int(window_seconds // step_seconds), 1)
    filters = ""
    if extra_filters:
        for i, col in enumerate(extra_filters, start=4):
            col_q = builder.column(col)
            filters += f" AND {col_q} = ${i}"
    inner = (
        f"SELECT time_bucket($3, {time_col}) AS bucket,"
        f"       {metric} AS count_bucket\n"
        f"FROM {table_q}\n"
        f"WHERE {time_col} >= $1 AND {time_col} < $2{filters}\n"
        "GROUP BY bucket"
    )
    query_str = f"""
        SELECT bucket,
               SUM(count_bucket) OVER (
                   ORDER BY bucket
                   ROWS BETWEEN {window_points - 1} PRECEDING AND CURRENT ROW
               ) AS value
        FROM ({inner}) AS sub
        ORDER BY bucket
        """
    sql, _ = builder.build(query_str, logger=LOG)
    return text(sql)


@monitor_query_performance()
async def fetch_time_buckets(
    pool: asyncpg.Pool,
    start: Any,
    end: Any,
    bucket_size: str = "1 hour",
    table: str = "access_events",
    metric: str = "COUNT(*)",
    time_column: str = "time",
    extra_filters: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Execute a time-bucketed query and return the results as dictionaries."""
    filter_keys = tuple(sorted(extra_filters.keys())) if extra_filters else None
    key = ("bucket", table, metric, time_column, filter_keys)
    query = _get_cached_plan(key)
    if query is None:
        query = build_time_bucket_query(
            bucket_size, table, metric, time_column, filter_keys
        )
        _cache_plan(key, query)
    builder = SecureQueryBuilder()
    params: List[Any] = [start, end, bucket_size]
    if extra_filters:
        params.extend(extra_filters[k] for k in filter_keys)  # type: ignore[arg-type]
    sql, params = builder.build(str(query), params, logger=LOG)
    rows = await pool.fetch(sql, *params)
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
    extra_filters: Dict[str, Any] | None = None,
) -> List[Dict[str, Any]]:
    """Execute a sliding-window aggregation and return the results."""
    filter_keys = tuple(sorted(extra_filters.keys())) if extra_filters else None
    key = (
        "window",
        window_seconds,
        table,
        metric,
        time_column,
        filter_keys,
    )
    query = _get_cached_plan(key)
    if query is None:
        query = build_sliding_window_query(
            window_seconds, step_seconds, table, metric, time_column, filter_keys
        )
        _cache_plan(key, query)
    builder = SecureQueryBuilder()
    params: List[Any] = [start, end, f"{step_seconds} seconds"]
    if extra_filters:
        params.extend(extra_filters[k] for k in filter_keys)  # type: ignore[arg-type]
    sql, params = builder.build(str(query), params, logger=LOG)
    rows = await pool.fetch(sql, *params)
    return [dict(r) for r in rows]


__all__ = [
    "build_time_bucket_query",
    "build_sliding_window_query",
    "fetch_time_buckets",
    "fetch_sliding_window",
]
