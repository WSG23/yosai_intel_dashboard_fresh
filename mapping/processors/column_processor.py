from __future__ import annotations

import pandas as pd

from mapping.core.interfaces import ProcessorInterface
from mapping.core.models import ProcessingResult
from mapping.processors.ai_processor import AIColumnMapperAdapter
from core.container import container as default_container
from typing import Any
from mapping.helpers import map_and_clean


class ColumnProcessor(ProcessorInterface):
    """Handle column mapping and cleanup for uploaded data."""

    def __init__(
        self,
        ai_adapter: AIColumnMapperAdapter | None = None,
        *,
        container: Any | None = None,
        default_model: str = "default",
    ) -> None:
        container = container or default_container
        self.ai_adapter = ai_adapter or AIColumnMapperAdapter(
            container=container, default_model=default_model
        )

    def process(
        self, df: pd.DataFrame, filename: str, *, model_key: str | None = None
    ) -> ProcessingResult:
        suggestions = self.ai_adapter.suggest(df, filename, model_key=model_key)
        cleaned = map_and_clean(df)
        return ProcessingResult(data=cleaned, suggestions=suggestions)
