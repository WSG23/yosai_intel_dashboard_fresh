from __future__ import annotations

from typing import Any

import pandas as pd

from core.unicode_utils import detect_surrogate_pairs, sanitize_for_utf8
from .validation_exceptions import ValidationError


class UnicodeSecurityValidator:
    """Validate and sanitize text or DataFrames for surrogate characters."""

    @staticmethod
    def validate_text(text: Any) -> str:
        sanitized = sanitize_for_utf8(text)
        if detect_surrogate_pairs(sanitized):
            raise ValidationError("Surrogate characters detected")
        return sanitized

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        sanitized = df.applymap(sanitize_for_utf8)
        if sanitized.select_dtypes(include=["object"]).applymap(
            detect_surrogate_pairs
        ).any().any():
            raise ValidationError("Surrogate characters detected")
        return sanitized


__all__ = ["UnicodeSecurityValidator"]
