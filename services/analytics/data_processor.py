"""Basic analytics data processor implementation."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from .protocols import DataProcessorProtocol


class DataProcessor(DataProcessorProtocol):
    """Minimal concrete implementation for the analytics pipeline."""

    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Return events unchanged."""
        return events

    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """Return data unchanged. ``rules`` are ignored."""
        return data

    def aggregate_data(
        self, data: pd.DataFrame, groupby: List[str], metrics: List[str]
    ) -> pd.DataFrame:
        """Return ``data`` without performing aggregation."""
        return data

    def validate_data_quality(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return a very basic data quality summary."""
        return {"rows": len(df)}

    def enrich_data(
        self, data: pd.DataFrame, enrichment_sources: List[str]
    ) -> pd.DataFrame:
        """Return data unchanged."""
        return data

    # ------------------------------------------------------------------
    # Extra helper used by legacy tests
    # ------------------------------------------------------------------
    def process_dataframe(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Compatibility shim calling :meth:`process_access_events`."""
        return self.process_access_events(df)
