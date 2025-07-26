"""Helpers for executing sanitized database queries."""

from __future__ import annotations

from database.secure_exec import execute_secure_query


__all__ = ["execute_secure_query"]


def execute_secure_query(conn: Any, query: str, params: Iterable[Any] | None = None) -> Any:
    """Encode ``query`` and ``params`` safely then execute using ``conn``."""
    sanitized_query = UnicodeQueryHandler.safe_encode_query(query)
    sanitized_params = UnicodeQueryHandler.safe_encode_params(params or ())
    return _exec_secure_query(conn, sanitized_query, sanitized_params)
