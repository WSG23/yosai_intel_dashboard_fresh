"""Security-focused wrapper around core Unicode utilities."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

import pandas as pd

from core.unicode_processor import (
    UnicodeProcessor,
    sanitize_unicode_input as core_sanitize_unicode_input,
)

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
            sanitized = core_sanitize_unicode_input(text)
            return unicodedata.normalize("NFKC", sanitized)
        except UnicodeError as exc:
            logger.warning("Unicode sanitization failed: %s", exc)
            cleaned = UnicodeProcessor.clean_surrogate_chars(text)
            try:
                cleaned = core_sanitize_unicode_input(cleaned)
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
        """Sanitize all string data within ``df`` and normalize."""
        logger = logging.getLogger(__name__)
        df_clean = UnicodeProcessor.sanitize_dataframe(df)

        # Normalize column names
        new_cols = []
        for col in df_clean.columns:
            if isinstance(col, str):
                try:
                    col = unicodedata.normalize("NFKC", col)
                except UnicodeError as exc:  # pragma: no cover - best effort
                    logger.warning("Column normalization failed: %s", exc)
                    col = col.encode("utf-8", "replace").decode("utf-8", "replace")
                    col = unicodedata.normalize("NFKC", col)
            new_cols.append(col)
        df_clean.columns = new_cols

        # Normalize string cells
        for col in df_clean.select_dtypes(include=["object"]).columns:
            def _norm(val: Any) -> Any:
                if isinstance(val, str):
                    try:
                        return unicodedata.normalize("NFKC", val)
                    except UnicodeError:
                        safe = val.encode("utf-8", "replace").decode("utf-8", "replace")
                        return unicodedata.normalize("NFKC", safe)
                return val

            df_clean[col] = df_clean[col].apply(_norm)

        return df_clean


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
