from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .base import MappingModel


class RuleBasedModel(MappingModel):
    """Simple rule based mapping model using predefined mappings."""

    def __init__(self, mappings: Dict[str, str] | None = None) -> None:
        super().__init__()
        self.mappings = mappings or {}

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        suggestions: Dict[str, Dict[str, Any]] = {}
        for col in df.columns:
            field = self.mappings.get(col, "")
            suggestions[col] = {"field": field, "confidence": 1.0 if field else 0.0}
        return suggestions
