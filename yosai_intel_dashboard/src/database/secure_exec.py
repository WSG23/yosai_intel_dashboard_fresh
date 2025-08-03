"""Secure wrappers for database execution with optional query caching."""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Iterable, Optional

from database.types import DBRows
from database.query_cache import QueryCache
from yosai_intel_dashboard.src.core.cache_manager import RedisCacheManager

logger = logging.getLogger(__name__)

_QUERY_CACHE: QueryCache | None = None


def get_query_cache(
    cache_manager: RedisCacheManager | None = None,
    *,
    ttl: int | None = None,
) -> QueryCache:
    """Return a shared :class:`QueryCache` instance.

    Parameters
    ----------
    cache_manager:
        Optional custom :class:`RedisCacheManager` to use as backend.
    ttl:
        Optional time-to-live override for cached results in seconds.
    """

    global _QUERY_CACHE
    if _QUERY_CACHE is None or cache_manager is not None or ttl is not None:
        _QUERY_CACHE = QueryCache(cache_manager=cache_manager, ttl=ttl)
    return _QUERY_CACHE


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
    optimize: bool = True,
):
    """Validate, optionally optimize and execute a SELECT query with caching."""

    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    p = _validate_params(params)

    cache = get_query_cache()
    key_data = {
        "sql": sql,
        "params": list(p) if p is not None else [],
        "opt": optimize,
    }
    cache_key = hashlib.sha256(
        json.dumps(key_data, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    cached = cache.get(cache_key)
    if cached is not None:
        return cached

    executable_sql = (
        _get_optimizer(conn).optimize_query(sql) if optimize else sql
    )
    logger.debug("Executing query: %s", executable_sql)
    if hasattr(conn, "execute_query"):
        result = conn.execute_query(executable_sql, p)
    elif hasattr(conn, "execute"):
        if p is not None:
            result = conn.execute(executable_sql, p)
        else:
            result = conn.execute(executable_sql)
    else:
        raise AttributeError("Object has no execute or execute_query method")

    cache.set(cache_key, result)
    return result


def execute_secure_query(conn: Any, sql: str, params: Iterable[Any]) -> DBRows:
    """Execute a parameterized SELECT query enforcing provided params."""
    if params is None:
        raise ValueError("params must be provided for execute_secure_query")
    return execute_query(conn, sql, params, optimize=False)


def execute_command(conn: Any, sql: str, params: Optional[Iterable[Any]] = None):
    """Validate, optimize and execute a modification command on ``conn``."""
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    p = _validate_params(params)
    optimized_sql = _get_optimizer(conn).optimize_query(sql)
    logger.debug("Executing command: %s", optimized_sql)
    if hasattr(conn, "execute_command"):
        return conn.execute_command(optimized_sql, p)
    if hasattr(conn, "execute"):
        if p is not None:
            return conn.execute(optimized_sql, p)
        return conn.execute(optimized_sql)
    raise AttributeError("Object has no execute or execute_command method")


__all__ = ["execute_query", "execute_command", "execute_secure_query", "get_query_cache"]
