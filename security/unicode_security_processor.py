"""Security-focused wrapper around core Unicode utilities."""

from __future__ import annotations

import logging
import unicodedata
from typing import Any

import pandas as pd

from core.unicode_processor import UnicodeProcessor


class UnicodeSecurityProcessor:
    """Expose safe Unicode helpers used by the security modules."""

    @staticmethod
    def sanitize_unicode_input(text: Any) -> str:
        """Return ``text`` with unsafe characters removed and normalized."""
        logger = logging.getLogger(__name__)
        try:
            if isinstance(text, bytes):
                text = text.decode("utf-8", errors="surrogatepass")
            else:
                text = str(text)
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to coerce %r to str: %s", text, exc)
            try:
                text = str(text)
            except Exception:
                return ""

        try:
            cleaned = UnicodeProcessor.clean_surrogate_chars(
                text, UnicodeProcessor.REPLACEMENT_CHAR
            )
            cleaned = unicodedata.normalize("NFKC", cleaned)
            return cleaned
        except UnicodeError as exc:
            logger.warning("Unicode normalization failed: %s", exc)
            try:
                cleaned = text.encode("utf-8", "replace").decode("utf-8", "replace")
                cleaned = UnicodeProcessor.clean_surrogate_chars(
                    cleaned, UnicodeProcessor.REPLACEMENT_CHAR
                )
                return unicodedata.normalize("NFKC", cleaned)
            except Exception as exc2:  # pragma: no cover - defensive
                logger.error("Fallback sanitization failed: %s", exc2)
                return ""

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
