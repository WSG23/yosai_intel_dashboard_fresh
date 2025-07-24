from __future__ import annotations

"""Helpers for executing sanitized database queries."""

from typing import Any, Optional

from unicode_toolkit import UnicodeQueryHandler
from database.secure_exec import execute_query as _execute_query


def execute_secure_query(conn: Any, query: str, params: Optional[tuple] = None):
    """Encode query and parameters then execute via :mod:`database.secure_exec`."""
    sanitized_query = UnicodeQueryHandler.safe_encode_query(query)
    sanitized_params = UnicodeQueryHandler.safe_encode_params(params)
    return _execute_query(conn, sanitized_query, sanitized_params)


__all__ = ["execute_secure_query"]
