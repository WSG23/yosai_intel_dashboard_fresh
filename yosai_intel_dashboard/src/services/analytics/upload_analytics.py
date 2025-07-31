"""Analytics helpers for uploaded DataFrame objects."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from yosai_intel_dashboard.src.services.analytics_summary import summarize_dataframe
from yosai_intel_dashboard.src.services.chunked_analysis import analyze_with_chunking
from yosai_intel_dashboard.src.services.upload_processing import (
    UploadAnalyticsProcessor as _UploadAnalyticsProcessor,
)
from validation.data_validator import DataValidator, DataValidatorProtocol


def summarize_dataframes(dfs: List[pd.DataFrame]) -> Dict[str, Any]:
    """Combine ``dfs`` and return a summary dictionary."""
    if not dfs:
        return {"status": "no_data"}
    combined = pd.concat(dfs, ignore_index=True)
    summary = summarize_dataframe(combined)
    summary.update({"status": "success", "files_processed": len(dfs)})
    return summary


def run_anomaly_detection(
    df: pd.DataFrame, validator: DataValidatorProtocol | None = None
) -> Dict[str, Any]:
    """Run anomaly detection using chunked analysis."""
    validator = validator or DataValidator(required_columns=["timestamp", "person_id"])
    return analyze_with_chunking(df, validator, ["anomaly"])


class UploadAnalyticsProcessor(_UploadAnalyticsProcessor):
    """Alias for :class:`services.upload_processing.UploadAnalyticsProcessor`."""


__all__ = [
    "summarize_dataframes",
    "run_anomaly_detection",
    "UploadAnalyticsProcessor",
]
