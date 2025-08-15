"""Compatibility wrappers delegating to :mod:`core.unicode`."""

from __future__ import annotations

from typing import Any, Iterable, Optional

import pandas as pd  # type: ignore[import]

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor as _UnicodeProcessor
from yosai_intel_dashboard.src.core.unicode import UnicodeSQLProcessor, sanitize_dataframe


class UnicodeProcessor:
    """Shim class preserving the previous interface."""

    def __init__(
        self, strategies: Optional[Iterable] = None
    ) -> None:  # pragma: no cover - compatibility
        pass

    def process(self, text: Any) -> str:
        return _UnicodeProcessor.safe_encode_text(text)

    def clean_surrogate_chars(self, text: Any) -> str:
        return _UnicodeProcessor.clean_surrogate_chars(str(text))

    def sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return sanitize_dataframe(df)

    def encode_sql_query(self, query: Any) -> str:
        return UnicodeSQLProcessor.encode_query(query)


__all__ = ["UnicodeProcessor"]
