from __future__ import annotations

import pandas as pd

from mapping.core.interfaces import ProcessorInterface
from mapping.core.models import ProcessingResult
from mapping.processors.ai_processor import AIColumnMapperAdapter
from utils.mapping_helpers import map_and_clean


class ColumnProcessor(ProcessorInterface):
    """Handle column mapping and cleanup for uploaded data."""

    def __init__(self, ai_adapter: AIColumnMapperAdapter | None = None) -> None:
        self.ai_adapter = ai_adapter or AIColumnMapperAdapter()

    def process(self, df: pd.DataFrame, filename: str) -> ProcessingResult:
        suggestions = self.ai_adapter.suggest(df, filename)
        cleaned = map_and_clean(df)
        return ProcessingResult(data=cleaned, suggestions=suggestions)
