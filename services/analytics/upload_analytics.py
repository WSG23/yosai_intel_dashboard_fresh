"""Analytics helpers for uploaded DataFrame objects."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from services.analytics import (
    analyze_with_chunking,
    generate_basic_analytics,
    map_and_clean,
    summarize_dataframe,
)
from services.data_validation import DataValidationService

from ..upload_processing import UploadAnalyticsProcessor as _UploadAnalyticsProcessor


def summarize_dataframes(dfs: List[pd.DataFrame]) -> Dict[str, Any]:
    """Combine ``dfs`` and return a summary dictionary."""
    if not dfs:
        return {"status": "no_data"}
    combined = pd.concat(dfs, ignore_index=True)
    summary = summarize_dataframe(combined)
    summary.update({"status": "success", "files_processed": len(dfs)})
    return summary


def run_anomaly_detection(df: pd.DataFrame, validator: DataValidationService) -> Dict[str, Any]:
    """Run anomaly detection using chunked analysis."""
    return analyze_with_chunking(df, validator, ["anomaly"])


class UploadAnalyticsProcessor(_UploadAnalyticsProcessor):
    """Alias for :class:`services.upload_processing.UploadAnalyticsProcessor`."""


__all__ = [
    "summarize_dataframes",
    "run_anomaly_detection",
    "UploadAnalyticsProcessor",
]

