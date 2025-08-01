from __future__ import annotations

from typing import Any

import pandas as pd

from yosai_intel_dashboard.src.core.container import container as default_container
from yosai_intel_dashboard.src.mapping.core.interfaces import ProcessorInterface
from yosai_intel_dashboard.src.mapping.core.models import ProcessingResult
from mapping.helpers import map_and_clean
from mapping.processors.ai_processor import AIColumnMapperAdapter



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
