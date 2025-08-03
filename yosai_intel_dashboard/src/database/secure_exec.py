"""Secure wrappers for database execution."""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

logger = logging.getLogger(__name__)


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


def execute_query(conn: Any, sql: str, params: Optional[Iterable[Any]] = None):
    """Validate, optimize and execute a SELECT query on ``conn``."""
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    p = _validate_params(params)
    optimized_sql = _get_optimizer(conn).optimize_query(sql)
    logger.debug("Executing query: %s", optimized_sql)
    if hasattr(conn, "execute_query"):
        return conn.execute_query(optimized_sql, p)
    if hasattr(conn, "execute"):
        if p is not None:
            return conn.execute(optimized_sql, p)
        return conn.execute(optimized_sql)
    raise AttributeError("Object has no execute or execute_query method")


def execute_secure_query(conn: Any, sql: str, params: Iterable[Any]) -> Any:
    """Execute a parameterized SELECT query enforcing provided params."""
    if params is None:
        raise ValueError("params must be provided for execute_secure_query")
    return execute_query(conn, sql, params)


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


__all__ = ["execute_query", "execute_command", "execute_secure_query"]
