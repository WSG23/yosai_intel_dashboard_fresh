from __future__ import annotations

"""Protocol definitions for controller components."""

from typing import Any, Dict, List, Protocol, runtime_checkable

import pandas as pd


@runtime_checkable
class UploadProcessingControllerProtocol(Protocol):
    """Interface for :class:`UploadProcessingController`."""

    def get_analytics_from_uploaded_data(self) -> Dict[str, Any]: ...

    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...

    def clean_uploaded_dataframe(self, df: pd.DataFrame) -> pd.DataFrame: ...

    def summarize_dataframe(self, df: pd.DataFrame) -> Dict[str, Any]: ...

    def analyze_with_chunking(
        self, df: pd.DataFrame, analysis_types: List[str]
    ) -> Dict[str, Any]: ...

    def diagnose_data_flow(self, df: pd.DataFrame) -> Dict[str, Any]: ...

    def process_uploaded_data_directly(
        self, uploaded_data: Dict[str, Any]
    ) -> Dict[str, Any]: ...

    def get_real_uploaded_data(self) -> Dict[str, Any]: ...

    def get_analytics_with_fixed_processor(self) -> Dict[str, Any]: ...


__all__ = ["UploadProcessingControllerProtocol"]
