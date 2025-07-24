from __future__ import annotations

"""Utilities for safely encoding SQL queries."""

from typing import Any

from .database_exceptions import UnicodeEncodingError

# from analytics_core.utils.unicode_processor import UnicodeHelper  # Circular import - use local implementation

class UnicodeHelper:
    """Fallback Unicode helper to break circular import"""
    
    @staticmethod
    def clean_text(text):
        """Simple Unicode cleaning"""
        if not isinstance(text, str):
            text = str(text)
        # Remove surrogate characters
        return ''.join(char for char in text if not (0xD800 <= ord(char) <= 0xDFFF))
    
    @staticmethod
    def safe_encode(text, encoding='utf-8'):
        """Safe encoding"""
        try:
            return text.encode(encoding)
        except UnicodeEncodeError:
            return text.encode(encoding, errors='replace')


# from core.unicode import contains_surrogates  # Circular import - use local implementation

def contains_surrogates(text):
    """Local implementation to break circular import"""
    if not isinstance(text, str):
        return False
    return any(0xD800 <= ord(char) <= 0xDFFF for char in text)




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
