from __future__ import annotations

"""Security-focused wrapper around core Unicode utilities."""

from typing import Any

import pandas as pd

from core.unicode_processor import UnicodeProcessor


class UnicodeSecurityProcessor:
    """Expose safe Unicode helpers used by the security modules."""

    @staticmethod
    def sanitize_unicode_input(text: Any) -> str:
        """Return ``text`` with unsafe characters removed."""
        return UnicodeProcessor.safe_encode_text(text)

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
