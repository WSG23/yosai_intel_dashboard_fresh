"""Secure wrappers for database execution with optional query caching."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from functools import lru_cache
from typing import Any, Iterable, Optional

try:  # optional import to avoid heavy dependency chain
    from core.performance import PerformanceThresholds
except Exception:  # pragma: no cover - default if core package unavailable
    class PerformanceThresholds:  # type: ignore[misc]
        SLOW_QUERY_SECONDS = 1.0

from database.performance_analyzer import DatabasePerformanceAnalyzer

from database.types import DBRows
from database.query_cache import QueryCache
from yosai_intel_dashboard.src.core.cache_manager import RedisCacheManager

try:  # optional Prometheus integration
    from database.metrics import query_execution_seconds
except Exception:  # pragma: no cover - metrics are optional
    query_execution_seconds = None  # type: ignore

logger = logging.getLogger(__name__)


@lru_cache(maxsize=1)
def _get_security_validator():
    from validation import security_validator as sv_mod

    if not hasattr(sv_mod, "redis_client"):
        sv_mod.redis_client = None  # type: ignore[attr-defined]
    return sv_mod.SecurityValidator(rate_limit=0, window_seconds=1, redis_client=None)

performance_analyzer = DatabasePerformanceAnalyzer()
query_metrics = performance_analyzer.query_metrics
SLOW_QUERY_THRESHOLD = float(
    os.getenv("DB_SLOW_QUERY_THRESHOLD", PerformanceThresholds.SLOW_QUERY_SECONDS)
)



def _infer_db_type(obj: Any) -> str:
    """Best-effort inference of database type from a connection or cursor."""
    name = obj.__class__.__name__.lower()
    module = obj.__class__.__module__.lower()
    if "sqlite" in name or "sqlite" in module:
        return "sqlite"
    parent = getattr(obj, "connection", None)
    if parent is not None:
        return _infer_db_type(parent)
    return "postgresql"


def _get_optimizer(obj: Any):
    """Return a cached :class:`DatabaseQueryOptimizer` for ``obj``."""
    optimizer = getattr(obj, "_optimizer", None)
    if optimizer is None:
        from database.query_optimizer import DatabaseQueryOptimizer

        optimizer = DatabaseQueryOptimizer(_infer_db_type(obj))
        try:
            setattr(obj, "_optimizer", optimizer)
        except Exception:
            pass
    return optimizer


def _validate_params(params: Optional[Iterable[Any]]) -> Optional[tuple]:
    if params is None:
        return None
    if isinstance(params, list):
        return tuple(params)
    if isinstance(params, tuple):
        return params
    raise TypeError("params must be a tuple/list or None")


def execute_query(
    conn: Any,
    sql: str,
    params: Optional[Iterable[Any]] = None,
    *,
    timeout: Optional[int] = None,
):

    """Validate, optimize and execute a SELECT query on ``conn``."""


    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    _get_security_validator().scan_query(sql)
    p = _validate_params(params)
    optimized_sql = _get_optimizer(conn).optimize_query(sql)
    logger.debug("Executing query: %s", optimized_sql)
    start = time.perf_counter()
    try:

        if hasattr(conn, "execute_query"):
            return conn.execute_query(optimized_sql, p)
        if hasattr(conn, "execute"):
            if p is not None:
                return conn.execute(optimized_sql, p)
            return conn.execute(optimized_sql)
        raise AttributeError("Object has no execute or execute_query method")
    finally:
        elapsed = time.perf_counter() - start
        performance_analyzer.analyze_query_performance(optimized_sql, elapsed)
        if elapsed > SLOW_QUERY_THRESHOLD:
            logger.warning("Slow query (%.6f s): %s", elapsed, optimized_sql)
        if query_execution_seconds is not None:
            query_execution_seconds.observe(elapsed)


def execute_secure_query(conn: Any, sql: str, params: Iterable[Any]) -> DBRows:
    """Execute a parameterized SELECT query enforcing provided params."""
    if params is None:
        raise ValueError("params must be provided for execute_secure_query")
    _get_security_validator().scan_query(sql)
    return execute_query(conn, sql, params)


def execute_command(
    conn: Any,
    sql: str,
    params: Optional[Iterable[Any]] = None,
    *,
    timeout: Optional[int] = None,
):
    """Validate, optimize and execute a modification command on ``conn``."""
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    _get_security_validator().scan_query(sql)
    p = _validate_params(params)
    optimized_sql = _get_optimizer(conn).optimize_query(sql)
    logger.debug("Executing command: %s", optimized_sql)
    start = time.perf_counter()
    try:

        if hasattr(conn, "execute_command"):
            return conn.execute_command(optimized_sql, p)
        if hasattr(conn, "execute"):
            if p is not None:
                return conn.execute(optimized_sql, p)
            return conn.execute(optimized_sql)
        raise AttributeError("Object has no execute or execute_command method")
    finally:
        elapsed = time.perf_counter() - start
        performance_analyzer.analyze_query_performance(optimized_sql, elapsed)
        if elapsed > SLOW_QUERY_THRESHOLD:
            logger.warning("Slow query (%.6f s): %s", elapsed, optimized_sql)
        if query_execution_seconds is not None:
            query_execution_seconds.observe(elapsed)


def execute_batch(
    conn: Any,
    sql: str,
    params_seq: Iterable[Iterable[Any]],
    *,
    timeout: Optional[int] = None,
):
    """Execute a batch of parameterized commands safely on ``conn``."""
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    _get_security_validator().scan_query(sql)
    pseq = [tuple(p) for p in params_seq]
    optimized_sql = _get_optimizer(conn).optimize_query(sql)
    logger.debug("Executing batch command: %s", optimized_sql)
    start = time.perf_counter()
    try:
        if hasattr(conn, "execute_batch"):
            return conn.execute_batch(optimized_sql, pseq)
        if hasattr(conn, "executemany"):
            return conn.executemany(optimized_sql, pseq)
        raise AttributeError("Object has no execute_batch or executemany method")
    finally:
        elapsed = time.perf_counter() - start
        performance_analyzer.analyze_query_performance(optimized_sql, elapsed)
        if elapsed > SLOW_QUERY_THRESHOLD:
            logger.warning("Slow query (%.6f s): %s", elapsed, optimized_sql)
        if query_execution_seconds is not None:
            query_execution_seconds.observe(elapsed)


__all__ = [
    "execute_query",
    "execute_command",
    "execute_batch",
    "execute_secure_query",
    "query_metrics",
    "performance_analyzer",

]
