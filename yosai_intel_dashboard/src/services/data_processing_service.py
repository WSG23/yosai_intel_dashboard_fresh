from __future__ import annotations

import pandas as pd

from services.analytics.data_processor import DataProcessor
from services.analytics.protocols import DataProcessorProtocol


class DataProcessingService(DataProcessorProtocol):
    """Thin wrapper around :class:`DataProcessor`."""

    def __init__(self) -> None:
        self._processor = DataProcessor()

    def process_access_events(self, events: pd.DataFrame) -> pd.DataFrame:
        return self._processor.process_access_events(events)

    def clean_data(self, data: pd.DataFrame, rules: dict | None = None) -> pd.DataFrame:
        return self._processor.clean_data(data, rules)

    def aggregate_data(
        self, data: pd.DataFrame, groupby: list[str], metrics: list[str]
    ) -> pd.DataFrame:
        return self._processor.aggregate_data(data, groupby, metrics)

    def validate_data_quality(self, data: pd.DataFrame) -> dict:
        return self._processor.validate_data_quality(data)

    def enrich_data(
        self, data: pd.DataFrame, enrichment_sources: list[str]
    ) -> pd.DataFrame:
        return self._processor.enrich_data(data, enrichment_sources)

    # compatibility helper used by some tests
    def process_dataframe(self, df: pd.DataFrame, config: dict) -> pd.DataFrame:
        return self._processor.process_dataframe(df, config)


__all__ = ["DataProcessingService"]
