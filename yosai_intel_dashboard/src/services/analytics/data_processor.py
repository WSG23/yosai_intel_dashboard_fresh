"""Basic analytics data processor implementation."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from .protocols import DataProcessorProtocol


class DataProcessor(DataProcessorProtocol):
    """Minimal concrete implementation for the analytics pipeline."""

    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame:
        """Apply preprocessing to ``events`` and return the result."""
        return self._standardize_missing(events)

    def clean_data(
        self, data: pd.DataFrame, rules: Dict[str, Any] | None = None
    ) -> pd.DataFrame:
        """Apply preprocessing to ``data``. ``rules`` are ignored."""
        return self._standardize_missing(data)

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
    # Preprocessing
    # ------------------------------------------------------------------
    def _standardize_missing(self, df: pd.DataFrame) -> pd.DataFrame:
        """Fill missing values for numeric and categorical columns.

        Numeric columns are filled with ``0`` while categorical columns are
        filled with the string ``"missing"``. A copy of ``df`` is returned to
        avoid mutating the caller's DataFrame.
        """
        df = df.copy()
        numeric_cols = df.select_dtypes(include="number").columns
        categorical_cols = df.select_dtypes(include=["object", "category"]).columns
        if len(numeric_cols):
            df[numeric_cols] = df[numeric_cols].fillna(0)
        if len(categorical_cols):
            df[categorical_cols] = df[categorical_cols].fillna("missing")
        return df

    # ------------------------------------------------------------------
    # Extra helper used by legacy tests
    # ------------------------------------------------------------------
    def process_dataframe(
        self, df: pd.DataFrame, config: Dict[str, Any]
    ) -> pd.DataFrame:
        """Compatibility shim calling :meth:`process_access_events`."""
        return self.process_access_events(df)
