"""Consolidated Unicode utilities for the Yosai project."""
from __future__ import annotations

import base64
import logging
import re
from typing import Any, Iterable, Optional, Tuple

from config.database_exceptions import UnicodeEncodingError

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Surrogate cleaning
# ---------------------------------------------------------------------------
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")


def clean_unicode_surrogates(text: Any) -> str:
    """Return ``text`` with Unicode surrogate characters removed."""

    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return ""

    return _SURROGATE_RE.sub("", text)


# ---------------------------------------------------------------------------
# Upload helpers
# ---------------------------------------------------------------------------

def decode_upload_content(content: str, filename: str) -> Tuple[bytes, str]:
    """Decode base64 upload content and return bytes and safe filename."""

    if not content:
        raise ValueError("No content provided")
    if "," in content:
        _, content = content.split(",", 1)
    try:
        decoded = base64.b64decode(content)
    except Exception as exc:
        logger.error("Failed to decode upload content: %s", exc)
        raise ValueError(f"Invalid file content: {exc}")
    return decoded, clean_unicode_surrogates(filename)


# ---------------------------------------------------------------------------
# SQL processing
# ---------------------------------------------------------------------------

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
            cleaned = clean_unicode_surrogates(query)
            cleaned.encode("utf-8")
            return cleaned
        except UnicodeEncodeError as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError("Failed to encode query", query) from exc
        except UnicodeDecodeError as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError("Failed to decode query", query) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise UnicodeEncodingError(str(exc), query) from exc


def contains_surrogates(text: Any) -> bool:
    if not isinstance(text, str):
        return False
    return any(0xD800 <= ord(char) <= 0xDFFF for char in text)


class UnicodeQueryHandler:
    """Utility for safely encoding SQL queries and parameters."""

    @staticmethod
    def _encode(value: Any) -> Any:
        if isinstance(value, str):
            try:
                return UnicodeSQLProcessor.encode_query(value)
            except UnicodeEncodingError:
                raise
            except Exception as exc:  # pragma: no cover - defensive
                raise UnicodeEncodingError(str(exc)) from exc
        if isinstance(value, dict):
            return {k: UnicodeQueryHandler._encode(v) for k, v in value.items()}
        if isinstance(value, (list, tuple, set)):
            return type(value)(UnicodeQueryHandler._encode(v) for v in value)
        return value

    @classmethod
    def safe_encode_query(cls, query: str) -> str:
        return cls._encode(query)

    @classmethod
    def safe_encode_params(cls, params: Any) -> Any:
        return cls._encode(params)


__all__ = [
    "clean_unicode_surrogates",
    "decode_upload_content",
    "UnicodeSQLProcessor",
    "UnicodeQueryHandler",
]
