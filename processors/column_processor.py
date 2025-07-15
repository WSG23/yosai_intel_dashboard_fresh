from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from mapping.core.interfaces import ProcessorInterface
from processors.ai_processor import AIColumnMapperAdapter
from utils.mapping_helpers import map_and_clean


class ColumnProcessor(ProcessorInterface):
    """Handle column mapping and cleanup for uploaded data."""

    def __init__(self, ai_adapter: AIColumnMapperAdapter | None = None) -> None:
        self.ai_adapter = ai_adapter or AIColumnMapperAdapter()

    def process(self, df: pd.DataFrame, filename: str) -> Dict[str, Any]:
        suggestions = self.ai_adapter.suggest(df, filename)
        cleaned = map_and_clean(df)
        return {"data": cleaned, "suggestions": suggestions}
