"""Utilities for cleaning Unicode surrogate characters."""
from __future__ import annotations

import logging
import pandas as pd
from pandas import DataFrame

_logger = logging.getLogger(__name__)


class UnicodeCleaner:
    """Helper class to remove invalid Unicode surrogate characters."""

    _SURROGATE_RANGE = (0xD800, 0xDFFF)

    @staticmethod
    def clean_string(text: str) -> str:
        """Return ``text`` with surrogate characters removed."""
        try:
            if not isinstance(text, str):
                text = str(text)
            cleaned = "".join(
                ch for ch in text if not (UnicodeCleaner._SURROGATE_RANGE[0] <= ord(ch) <= UnicodeCleaner._SURROGATE_RANGE[1])
            )
            return cleaned
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Error cleaning string: %s", exc)
            return text

    @staticmethod
    def clean_dataframe(df: DataFrame) -> DataFrame:
        """Return a copy of ``df`` with surrogate characters removed."""
        try:
            df_clean = df.copy()
            # Clean column names
            df_clean.columns = [UnicodeCleaner.clean_string(c) for c in df_clean.columns]
            # Clean string values
            for col in df_clean.select_dtypes(include=["object"]).columns:
                df_clean[col] = df_clean[col].map(UnicodeCleaner.clean_string)
            return df_clean
        except Exception as exc:  # pragma: no cover - best effort
            _logger.error("Error cleaning DataFrame: %s", exc)
            return df

__all__ = ["UnicodeCleaner"]
