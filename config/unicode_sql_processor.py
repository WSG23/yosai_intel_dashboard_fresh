from __future__ import annotations

"""Utilities for safely encoding SQL queries."""

from typing import Any

from .database_exceptions import UnicodeEncodingError
from analytics_core.utils.unicode_processor import UnicodeHelper
from core.unicode import contains_surrogates


class UnicodeSQLProcessor:
    """Encode SQL queries while handling surrogate escapes."""

    @staticmethod
    def encode_query(query: Any) -> str:
        """Return ``query`` encoded for safe SQL execution."""
        if not isinstance(query, str):
            query = str(query)
        if contains_surrogates(query):
            raise UnicodeEncodingError("Surrogate characters detected", query)
        try:
            cleaned = UnicodeHelper.clean_text(query)
            cleaned.encode("utf-8")
            return cleaned
        except UnicodeEncodeError as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError("Failed to encode query", query) from exc
        except UnicodeDecodeError as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError("Failed to decode query", query) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError(str(exc), query) from exc


__all__ = ["UnicodeSQLProcessor"]
