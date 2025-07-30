from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from .controllers.upload_controller import UploadProcessingController


class DataHandler:
    """Load, clean and summarize uploaded data."""

    def __init__(self, controller: UploadProcessingController) -> None:
        self.controller = controller

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Return uploaded dataframes keyed by filename."""
        return self.controller.load_uploaded_data()

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Return ``df`` after applying standard cleaning."""
        return self.controller.clean_uploaded_dataframe(df)

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Return a summary dictionary for ``df``."""
        return self.controller.summarize_dataframe(df)

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]:
        """Analyze ``df`` using chunked processing."""
        return self.controller.analyze_with_chunking(df, analysis_types)

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Run diagnostic checks on ``df``."""
        return self.controller.diagnose_data_flow(df)

    def get_real_uploaded_data(self) -> Dict[str, Any]:
        """Load and summarize all uploaded records."""
        return self.controller.get_real_uploaded_data()

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]:
        """Return analytics using the sample file processor."""
        return self.controller.get_analytics_with_fixed_processor()


__all__ = ["DataHandler"]
