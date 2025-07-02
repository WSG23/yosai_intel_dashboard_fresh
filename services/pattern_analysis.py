"""Helper functions for unique pattern analysis used by AnalyticsService."""
from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)


def load_patterns_data(service: Any, data_source: str | None) -> Tuple[pd.DataFrame, int]:
    """Load and clean data for unique patterns analysis via the given service."""
    if data_source == "database":
        df, _meta = service.data_loader.get_processed_database()
        uploaded_data = {"database": df} if not df.empty else {}
    else:
        uploaded_data = service.load_uploaded_data()
    if not uploaded_data:
        return pd.DataFrame(), 0
    all_dfs: List[pd.DataFrame] = []
    total_original_rows = 0
    for filename, df in uploaded_data.items():
        total_original_rows += len(df)
        cleaned_df = service.clean_uploaded_dataframe(df)
        all_dfs.append(cleaned_df)
    combined_df = all_dfs[0] if len(all_dfs) == 1 else pd.concat(all_dfs, ignore_index=True)
    return combined_df, total_original_rows


def calculate_pattern_stats(df: pd.DataFrame) -> Tuple[int, int, int, int]:
    """Calculate record, user, device and date span statistics."""
    total_records = len(df)
    unique_users = df["person_id"].nunique() if "person_id" in df.columns else 0
    unique_devices = df["door_id"].nunique() if "door_id" in df.columns else 0
    date_span = 0
    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        valid_dates = df["timestamp"].dropna()
        if len(valid_dates) > 0:
            date_span = (valid_dates.max() - valid_dates.min()).days
    return total_records, unique_users, unique_devices, date_span


def calculate_success_rate(df: pd.DataFrame) -> float:
    """Calculate overall access success rate."""
    if "access_result" in df.columns:
        success_mask = (
            df["access_result"].str.lower().str.contains("grant|allow|success|permit", case=False, na=False)
        )
        return success_mask.mean()
    return 0.0

__all__ = [
    "load_patterns_data",
    "calculate_pattern_stats",
    "calculate_success_rate",
]
