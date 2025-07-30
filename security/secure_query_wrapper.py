from __future__ import annotations

"""High level secure SQL execution helpers."""

import logging
from typing import Any, Iterable, Optional

from database.secure_exec import execute_command, execute_query

logger = logging.getLogger(__name__)


def execute_secure_sql(
    conn: Any, query: str, params: Optional[Iterable[Any]] = None
) -> Any:
    """Safely execute a read query using parameterization."""
    if not isinstance(query, str):
        raise TypeError("query must be a string")
    from core.unicode import UnicodeSQLProcessor, clean_unicode_surrogates

    sanitized_query = UnicodeSQLProcessor.encode_query(query)
    sanitized_params = None
    if params is not None:
        sanitized_params = tuple(
            UnicodeSQLProcessor.encode_query(p) if isinstance(p, str) else p
            for p in params
        )
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
    from core.unicode import UnicodeSQLProcessor, clean_unicode_surrogates

    sanitized_cmd = UnicodeSQLProcessor.encode_query(command)
    sanitized_params = None
    if params is not None:
        sanitized_params = tuple(
            UnicodeSQLProcessor.encode_query(p) if isinstance(p, str) else p
            for p in params
        )
    logger.debug("Executing command: %s", sanitized_cmd)
    try:
        return execute_command(conn, sanitized_cmd, sanitized_params)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error("Command failed: %s", clean_unicode_surrogates(exc))
        raise


__all__ = ["execute_secure_sql", "execute_secure_command"]
