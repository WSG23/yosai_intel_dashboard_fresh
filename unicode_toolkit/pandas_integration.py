from __future__ import annotations

"""Pandas helpers for Unicode sanitization."""

from typing import Callable, Optional

import pandas as pd

from yosai_intel_dashboard.src.core.unicode import sanitize_dataframe as _sanitize_dataframe


def sanitize_dataframe(
    df: pd.DataFrame,
    processor: Optional[object] = None,
    progress: Optional[Callable[[int, int], None]] = None,
) -> pd.DataFrame:
    """Return a sanitized copy of ``df``."""

    # ``processor`` and ``progress`` are kept for backwards compatibility
    return _sanitize_dataframe(df)


__all__ = ["sanitize_dataframe"]
