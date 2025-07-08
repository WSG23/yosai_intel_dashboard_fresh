from __future__ import annotations

"""Unicode handling utilities specialized for text, SQL and security."""

import logging
import re
import unicodedata
from typing import Any

logger = logging.getLogger(__name__)

# Precompiled regular expressions for performance
_CONTROL_RE = re.compile(r"[\x00-\x1F\x7F]")
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")


class UnicodeTextProcessor:
    """Clean and normalize arbitrary text.

    Additional utilities like :func:`core.unicode.object_count` help analyze
    collections of strings.
    """

    @staticmethod
    def clean_text(text: Any) -> str:
        """Return ``text`` stripped of control codes and surrogates."""
        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as exc:  # pragma: no cover - defensive
                logger.error("Failed to convert text to str: %s", exc)
                return ""

        try:
            text = unicodedata.normalize("NFKC", text)
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning("Unicode normalization failed: %s", exc)

        try:
            text = _SURROGATE_RE.sub("", text)
            text = _CONTROL_RE.sub("", text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.error("Regex cleanup failed: %s", exc)
            text = "".join(
                ch
                for ch in text
                if not (0xD800 <= ord(ch) <= 0xDFFF or ord(ch) < 32 or ord(ch) == 0x7F)
            )

        return text


class UnicodeSQLProcessor:
    """Safely encode SQL queries with Unicode handling."""

    @staticmethod
    def encode_query(query: Any) -> str:
        """Return ``query`` encoded for safe SQL execution."""
        cleaned = UnicodeTextProcessor.clean_text(query)
        try:
            cleaned.encode("utf-8")
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Unicode encode failed: %s", exc)
            cleaned = cleaned.encode("utf-8", "ignore").decode("utf-8", "ignore")
        return cleaned


class UnicodeSecurityProcessor:
    """Sanitize input for security sensitive contexts."""

    _HTML_REPLACEMENTS = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#x27;",
        "/": "&#x2F;",
    }

    @staticmethod
    def sanitize_input(text: Any) -> str:
        """Return ``text`` sanitized for safe handling."""
        sanitized = UnicodeTextProcessor.clean_text(text)
        for char, repl in UnicodeSecurityProcessor._HTML_REPLACEMENTS.items():
            sanitized = sanitized.replace(char, repl)
        return sanitized


__all__ = [
    "UnicodeTextProcessor",
    "UnicodeSQLProcessor",
    "UnicodeSecurityProcessor",
]
