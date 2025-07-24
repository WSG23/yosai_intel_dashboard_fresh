from __future__ import annotations

from typing import Any, Dict

import time

from core.performance import MetricType, get_performance_monitor

import pandas as pd


class AIColumnMapperAdapter:
    """Thin wrapper around the :class:`ComponentPluginAdapter` plugin system."""

    def __init__(self, adapter: Any | None = None, monitor=None) -> None:
        if adapter is None:
            from components.plugin_adapter import ComponentPluginAdapter

            adapter = ComponentPluginAdapter()
        self._adapter = adapter
        self._monitor = monitor or get_performance_monitor()

    def suggest(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict[str, Any]]:
        """Return AI suggestions for *df* columns and record metrics."""
        start = time.time()
        suggestions = self._adapter.get_ai_column_suggestions(df, filename)
        duration = time.time() - start
        self._monitor.record_metric(
            "column_mapping.mapping_time",
            duration,
            MetricType.FILE_PROCESSING,
            tags={"filename": filename},
        )
        for col, info in suggestions.items():
            confidence = None
            if isinstance(info, dict):
                confidence = info.get("confidence")
            if confidence is not None:
                self._monitor.record_metric(
                    "column_mapping.confidence",
                    confidence,
                    MetricType.FILE_PROCESSING,
                    tags={"column": col, "field": str(info.get("field", ""))},
                )
        return suggestions

    def confirm(
        self, filename: str, mapping: Dict[str, str], metadata: Dict[str, Any]
    ) -> bool:
        """Store confirmed column mapping for *filename*."""
        return self._adapter.save_verified_mappings(filename, mapping, metadata)
