from __future__ import annotations

from typing import Any

import pandas as pd

from .unicode_security_processor import UnicodeSecurityProcessor
from .validation_exceptions import ValidationError
from core.unicode_processor import contains_surrogates


class UnicodeSecurityValidator:
    """Validate and sanitize text or DataFrames for surrogate characters."""

    @staticmethod
    def validate_text(text: Any) -> str:
        sanitized = UnicodeSecurityProcessor.sanitize_unicode_input(text)
        if contains_surrogates(sanitized):
            raise ValidationError("Surrogate characters detected")
        return sanitized

    @staticmethod
    def validate_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        sanitized = UnicodeSecurityProcessor.sanitize_dataframe(df)
        if sanitized.select_dtypes(include=["object"]).applymap(
            lambda x: contains_surrogates(str(x))
        ).any().any():
            raise ValidationError("Surrogate characters detected")
        return sanitized


__all__ = ["UnicodeSecurityValidator"]
