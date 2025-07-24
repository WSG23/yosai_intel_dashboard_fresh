from __future__ import annotations

"""Pandas helpers for Unicode sanitization."""

from typing import Callable, Optional

import pandas as pd

from .core import UnicodeProcessor


def sanitize_dataframe(
    df: pd.DataFrame,
    processor: Optional[UnicodeProcessor] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> pd.DataFrame:
    """Return a copy of ``df`` with all text columns sanitized."""

    if processor is None:
        processor = UnicodeProcessor()

    clean = df.copy()
    clean.columns = [
        processor.process(c) if isinstance(c, str) else c for c in clean.columns
    ]

    obj_cols = clean.select_dtypes(include=["object"]).columns
    total = len(obj_cols)
    for idx, col in enumerate(obj_cols, 1):
        clean[col] = clean[col].apply(
            lambda x: processor.process(x) if pd.notna(x) else x
        )
        if progress:
            progress(idx, total)

    return clean


__all__ = ["sanitize_dataframe"]
