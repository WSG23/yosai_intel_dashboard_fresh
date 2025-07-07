from __future__ import annotations

from typing import Dict

import pandas as pd

from column_standardizer import standardize_column_names


class AIColumnMapperAdapter:
    """Adapter that maps columns using AI suggestions then standardizes names."""

    def __init__(self, adapter: object | None = None) -> None:
        if adapter is None:
            from components.plugin_adapter import ComponentPluginAdapter
            adapter = ComponentPluginAdapter()
        self.adapter = adapter

    def map_and_standardize(self, df: pd.DataFrame) -> pd.DataFrame:
        try:
            suggestions: Dict[str, str] = self.adapter.suggest_columns(df.columns.tolist())
        except Exception:
            suggestions = {}
        mapping = {src: dest for src, dest in suggestions.items() if dest}
        mapped = df.rename(columns=mapping)
        return standardize_column_names(mapped)


__all__ = ["AIColumnMapperAdapter"]
