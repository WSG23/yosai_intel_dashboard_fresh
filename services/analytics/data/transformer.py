from __future__ import annotations

"""Dataframe transformation helpers."""

from typing import Any, Dict

import pandas as pd


class DataTransformer:
    """Simple dataframe transformer used in tests."""

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        return df

    def summarize(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {"rows": len(df), "columns": list(df.columns)}

    def diagnose(self, df: pd.DataFrame) -> Dict[str, Any]:
        return {"rows": len(df)}


__all__ = ["DataTransformer"]
