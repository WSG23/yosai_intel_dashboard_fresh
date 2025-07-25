from typing import Any, Dict, List

import pandas as pd

from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.services.analytics.upload_analytics import (
    UploadAnalyticsProcessor,
)
from yosai_intel_dashboard.src.services.data_processing.processor import Processor
from yosai_intel_dashboard.src.services.interfaces import get_upload_data_service
from yosai_intel_dashboard.src.services.upload_data_service import UploadDataService


class UploadProcessingController:
    """Delegate upload related operations to :class:`UploadAnalyticsProcessor`."""

    def __init__(
        self,
        validator: SecurityValidator,
        processor: Processor,
        upload_data_service: UploadDataService | None = None,
    ) -> None:
        self.validator = validator
        self.processor = processor
        self.upload_data_service = upload_data_service or get_upload_data_service()
        self.upload_processor = UploadAnalyticsProcessor(self.validator, self.processor)

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]:
        return self.upload_processor.get_analytics_from_uploaded_data()

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        if self.upload_data_service:
            return self.upload_data_service.get_uploaded_data()
        return self.upload_processor.load_uploaded_data()

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.upload_processor.clean_uploaded_dataframe(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        return self.upload_processor.summarize_dataframe(df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        return self.upload_processor.analyze_with_chunking(df, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        return self.upload_processor.diagnose_data_flow(df)

    def process_uploaded_data_directly(
        self, uploaded_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        return self.upload_processor._process_uploaded_data_directly(uploaded_data)

    def get_real_uploaded_data(self) -> Dict[str, Any]:
        return self.upload_processor._get_real_uploaded_data()

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        return self.upload_processor._get_analytics_with_fixed_processor()


__all__ = ["UploadProcessingController"]
