"""Compatibility wrappers for SQL Unicode handling."""

from __future__ import annotations

from typing import Any
import warnings

from .database_exceptions import UnicodeEncodingError


class UnicodeSQLProcessor:
    """Deprecated wrapper around :class:`core.unicode.UnicodeSQLProcessor`."""

    @staticmethod
    def encode_query(query: Any) -> str:
        warnings.warn(
            "config.unicode_sql_processor.UnicodeSQLProcessor is deprecated; "
            "use core.unicode.UnicodeSQLProcessor",
            DeprecationWarning,
            stacklevel=2,
        )

        from core import unicode as _unicode  # Local import to avoid circulars

        if _unicode.contains_surrogates(str(query)):
            raise UnicodeEncodingError("Surrogate characters detected", query)

        return _unicode.UnicodeSQLProcessor.encode_query(query)


__all__ = ["UnicodeSQLProcessor"]

