from __future__ import annotations

"""Simplified Unicode helpers reused across analytics core."""

import pandas as pd
from core.unicode import UnicodeProcessor


class UnicodeHelper(UnicodeProcessor):
    """Expose :class:`core.unicode.UnicodeProcessor` under ``analytics.core``."""

    @staticmethod
    def clean_text(text: str, replacement: str = "") -> str:  # type: ignore[override]
        return UnicodeProcessor.clean_text(text, replacement)

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:  # type: ignore[override]
        return UnicodeProcessor.sanitize_dataframe(df)


__all__ = ["UnicodeHelper"]

