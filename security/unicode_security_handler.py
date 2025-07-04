from __future__ import annotations

"""Security-focused Unicode handling utilities."""

from typing import Any

import pandas as pd

from core.unicode_utils import sanitize_unicode_input as _sanitize_input
from utils.unicode_utils import sanitize_dataframe as _sanitize_dataframe


class UnicodeSecurityHandler:
    """Centralized Unicode sanitization for security modules."""

    @staticmethod
    def sanitize_unicode_input(text: Any) -> str:
        """Sanitize input text for unsafe Unicode characters."""
        return _sanitize_input(text)

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize all string data within a DataFrame."""
        return _sanitize_dataframe(df)


__all__ = ["UnicodeSecurityHandler"]
