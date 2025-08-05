"""Secure wrappers for database execution with optional query caching."""

from __future__ import annotations

import logging
import os
import time
from functools import lru_cache
from typing import Any, Iterable, Optional

try:  # optional import to avoid heavy dependency chain
    from core.performance import PerformanceThresholds as _PerfThresh

    _SLOW_DEFAULT = getattr(_PerfThresh, "SLOW_QUERY_SECONDS", 1.0)
except Exception:  # pragma: no cover - default if core package unavailable
    _SLOW_DEFAULT = 1.0

from yosai_intel_dashboard.src.database.performance_analyzer import (
    DatabasePerformanceAnalyzer,
)
from yosai_intel_dashboard.src.database.types import DBRows

try:  # optional Prometheus integration
    from yosai_intel_dashboard.src.database.metrics import query_execution_seconds
except Exception:  # pragma: no cover - metrics are optional
    query_execution_seconds = None  # type: ignore

logger = logging.getLogger(__name__)


class DatabaseSettings:
    """Simple configuration holder used for query timeouts."""

    query_timeout_seconds: int = 0


@lru_cache(maxsize=1)
def _get_security_validator():
    try:
        from validation import security_validator as sv_mod

        if not hasattr(sv_mod, "redis_client"):
            sv_mod.redis_client = None  # type: ignore[attr-defined]
        return sv_mod.SecurityValidator(
            rate_limit=0, window_seconds=1, redis_client=None
        )
    except Exception:  # pragma: no cover - lightweight fallback

        class _DummyValidator:
            def scan_query(self, _sql: str) -> None:  # noqa: D401 - simple stub
                """No-op validator used when security module is unavailable."""

        return _DummyValidator()


performance_analyzer = DatabasePerformanceAnalyzer()
query_metrics = performance_analyzer.query_metrics
SLOW_QUERY_THRESHOLD = float(os.getenv("DB_SLOW_QUERY_THRESHOLD", _SLOW_DEFAULT))


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
        from yosai_intel_dashboard.src.database.query_optimizer import (
            DatabaseQueryOptimizer,
        )

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
    timeout_seconds = getattr(DatabaseSettings, "query_timeout_seconds", 0)
    db_type = _infer_db_type(conn)
    start = time.perf_counter()
    if timeout_seconds:
        ms = int(timeout_seconds * 1000)
        try:
            if db_type == "postgresql":
                try:
                    conn.execute("SET LOCAL statement_timeout = %s", (ms,))
                except Exception:
                    conn.execute(f"SET LOCAL statement_timeout = {int(ms)}")
            elif db_type == "sqlite":
                try:
                    conn.execute("PRAGMA busy_timeout = ?", (ms,))
                except Exception:
                    conn.execute(f"PRAGMA busy_timeout = {int(ms)}")
        except Exception:
            pass  # pragma: no cover - best effort
    try:
        if hasattr(conn, "execute_query"):
            result = conn.execute_query(optimized_sql, p)
        elif hasattr(conn, "execute"):
            if p is not None:
                result = conn.execute(optimized_sql, p)
            else:
                result = conn.execute(optimized_sql)
        else:
            raise AttributeError("Object has no execute or execute_query method")
        return result
    finally:
        if timeout_seconds:
            try:
                if db_type == "postgresql":
                    conn.execute("SET LOCAL statement_timeout = DEFAULT")
                elif db_type == "sqlite":
                    conn.execute("PRAGMA busy_timeout = 0")
            except Exception:
                pass  # pragma: no cover - best effort
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
    pseq = (tuple(p) for p in params_seq)
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
