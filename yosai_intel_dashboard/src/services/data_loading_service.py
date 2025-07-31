from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pandas as pd

from yosai_intel_dashboard.src.services.analytics.data.loader import DataLoader
from yosai_intel_dashboard.src.services.analytics.protocols import DataLoadingProtocol
from yosai_intel_dashboard.src.core.interfaces.service_protocols import AnalyticsDataLoaderProtocol
from services.controllers.upload_controller import UploadProcessingController
from yosai_intel_dashboard.src.services.data_processing.processor import Processor


class DataLoadingService(DataLoadingProtocol, AnalyticsDataLoaderProtocol):
    """Service providing data loading utilities for analytics."""

    def __init__(
        self, controller: UploadProcessingController, processor: Processor
    ) -> None:
        self._loader = DataLoader(controller, processor)

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self._loader.load_uploaded_data()

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return self._loader.clean_uploaded_dataframe(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        return self._loader.summarize_dataframe(df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        return self._loader.analyze_with_chunking(df, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        return self._loader.diagnose_data_flow(df)

    def get_real_uploaded_data(self) -> Dict[str, Any]:
        return self._loader.get_real_uploaded_data()

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        return self._loader.get_analytics_with_fixed_processor()

    def load_patterns_dataframe(
        self, data_source: str | None
    ) -> Tuple[pd.DataFrame, int]:
        return self._loader.load_patterns_dataframe(data_source)


__all__ = ["DataLoadingService"]
