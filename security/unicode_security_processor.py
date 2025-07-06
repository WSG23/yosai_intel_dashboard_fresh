"""Security-focused wrapper around core Unicode utilities."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

import pandas as pd

from core.unicode_processor import UnicodeProcessor

logger = logging.getLogger(__name__)


class UnicodeSecurityProcessor:
    """Expose safe Unicode helpers used by the security modules."""

    @staticmethod
    def sanitize_unicode_input(text: Any) -> str:
        """Return ``text`` normalized and stripped of surrogate codepoints."""

        if not isinstance(text, str):
            try:
                text = str(text)
            except Exception as exc:  # pragma: no cover - defensive
                logger.warning("Failed to convert %r to str: %s", text, exc)
                return ""

        try:
            sanitized = UnicodeProcessor.sanitize_unicode_input(text)
            return unicodedata.normalize("NFKC", sanitized)
        except UnicodeError as exc:
            logger.warning("Unicode sanitization failed: %s", exc)
            cleaned = UnicodeProcessor.clean_surrogate_chars(text)
            try:
                cleaned = UnicodeProcessor.sanitize_unicode_input(cleaned)
                return unicodedata.normalize("NFKC", cleaned)
            except Exception as inner:
                logger.error("Normalization retry failed: %s", inner)
                return cleaned
        except Exception as exc:  # pragma: no cover - extreme defensive
            logger.error("sanitize_unicode_input failed: %s", exc)
            return "".join(
                ch for ch in str(text) if not (0xD800 <= ord(ch) <= 0xDFFF)
            )

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize all string data within ``df``."""
        return UnicodeProcessor.sanitize_dataframe(df)


# Module-level helpers for convenience ---------------------------------

def sanitize_unicode_input(text: Any) -> str:
    return UnicodeSecurityProcessor.sanitize_unicode_input(text)


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    return UnicodeSecurityProcessor.sanitize_dataframe(df)


__all__ = [
    "UnicodeSecurityProcessor",
    "sanitize_unicode_input",
    "sanitize_dataframe",
]
