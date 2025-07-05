from __future__ import annotations

"""Utilities for safely encoding SQL queries."""

from typing import Any

from .database_exceptions import UnicodeEncodingError


class UnicodeSQLProcessor:
    """Encode SQL queries while handling surrogate escapes."""

    @staticmethod
    def encode_query(query: Any) -> str:
        """Return ``query`` encoded for safe SQL execution."""
        if not isinstance(query, str):
            query = str(query)
        try:
            data = query.encode("utf-8", "surrogateescape")
            return data.decode("utf-8", "replace")
        except Exception as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError(str(exc)) from exc


__all__ = ["UnicodeSQLProcessor"]
