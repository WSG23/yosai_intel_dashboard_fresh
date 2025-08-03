"""Secure wrappers for database execution."""

from __future__ import annotations

import logging
from typing import Any, Iterable, Optional

from database.types import DBRows

logger = logging.getLogger(__name__)


def _validate_params(params: Optional[Iterable[Any]]) -> Optional[tuple]:
    if params is None:
        return None
    if isinstance(params, list):
        return tuple(params)
    if isinstance(params, tuple):
        return params
    raise TypeError("params must be a tuple/list or None")


def execute_query(
    conn: Any, sql: str, params: Optional[Iterable[Any]] = None
) -> DBRows:
    """Validate and execute a SELECT query on the given connection."""
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    p = _validate_params(params)
    logger.debug("Executing query: %s", sql)
    if hasattr(conn, "execute_query"):
        return conn.execute_query(sql, p)
    if hasattr(conn, "execute"):
        if p is not None:
            return conn.execute(sql, p)
        return conn.execute(sql)
    raise AttributeError("Object has no execute or execute_query method")


def execute_secure_query(conn: Any, sql: str, params: Iterable[Any]) -> DBRows:
    """Execute a parameterized SELECT query enforcing provided params."""
    if params is None:
        raise ValueError("params must be provided for execute_secure_query")
    return execute_query(conn, sql, params)


def execute_command(conn: Any, sql: str, params: Optional[Iterable[Any]] = None):
    """Validate and execute a modification command on the given connection."""
    if not isinstance(sql, str):
        raise TypeError("sql must be a string")
    p = _validate_params(params)
    logger.debug("Executing command: %s", sql)
    if hasattr(conn, "execute_command"):
        return conn.execute_command(sql, p)
    if hasattr(conn, "execute"):
        if p is not None:
            return conn.execute(sql, p)
        return conn.execute(sql)
    raise AttributeError("Object has no execute or execute_command method")


__all__ = ["execute_query", "execute_command", "execute_secure_query"]
