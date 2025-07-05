from __future__ import annotations

"""Security-focused Unicode handling utilities."""

from typing import Any

import pandas as pd

from core.unicode_processor import UnicodeProcessor


class UnicodeSecurityHandler:
    """Centralized Unicode sanitization for security modules."""

    @staticmethod
    def sanitize_unicode_input(text: Any) -> str:
        """Sanitize input text for unsafe Unicode characters."""
        return UnicodeProcessor.safe_encode(text).text

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize all string data within a DataFrame."""
        return UnicodeProcessor.sanitize_dataframe(df)


__all__ = ["UnicodeSecurityHandler"]
