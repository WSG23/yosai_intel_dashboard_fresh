from __future__ import annotations

"""Security-focused Unicode handling utilities."""

from typing import Any

import pandas as pd

from .unicode_security_processor import UnicodeSecurityProcessor


class UnicodeSecurityHandler:
    """Backward compatibility wrapper for :class:`UnicodeSecurityProcessor`."""

    @staticmethod
    def sanitize_unicode_input(text: Any) -> str:
        return UnicodeSecurityProcessor.sanitize_unicode_input(text)

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        return UnicodeSecurityProcessor.sanitize_dataframe(df)


__all__ = ["UnicodeSecurityHandler"]
