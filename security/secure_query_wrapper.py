from __future__ import annotations

"""High level secure SQL execution helpers."""

import logging
from typing import Any, Iterable, Optional

from unicode_toolkit import UnicodeQueryHandler, clean_unicode_surrogates
from database.secure_exec import execute_query, execute_command

logger = logging.getLogger(__name__)


def execute_secure_sql(
    conn: Any, query: str, params: Optional[Iterable[Any]] = None
) -> Any:
    """Safely execute a read query using parameterization."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    sanitized_query = UnicodeQueryHandler.safe_encode_query(query)
    sanitized_params = UnicodeQueryHandler.safe_encode_params(params)
    logger.debug("Executing query: %s", sanitized_query)
    try:
        return execute_query(conn, sanitized_query, sanitized_params)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Query failed: %s", clean_unicode_surrogates(exc))
        raise


def execute_secure_command(
    conn: Any, command: str, params: Optional[Iterable[Any]] = None
) -> Any:
    """Safely execute an INSERT/UPDATE/DELETE using parameterization."""
    if not isinstance(command, str):
        raise TypeError("command must be a string")
    sanitized_cmd = UnicodeQueryHandler.safe_encode_query(command)
    sanitized_params = UnicodeQueryHandler.safe_encode_params(params)
    logger.debug("Executing command: %s", sanitized_cmd)
    try:
        return execute_command(conn, sanitized_cmd, sanitized_params)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Command failed: %s", clean_unicode_surrogates(exc))
        raise


__all__ = ["execute_secure_sql", "execute_secure_command"]
