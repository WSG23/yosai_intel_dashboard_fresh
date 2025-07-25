from __future__ import annotations

"""Data enhancement helpers wrapping :class:`UnicodeProcessor`."""

from typing import Any

import pandas as pd

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame using :class:`UnicodeProcessor`."""
    return UnicodeProcessor.sanitize_dataframe(df)


def clean_unicode_text(text: str) -> str:
    """Clean text by removing surrogate characters."""
    return UnicodeProcessor.clean_surrogate_chars(text)


__all__ = ["UnicodeProcessor", "sanitize_dataframe", "clean_unicode_text"]
