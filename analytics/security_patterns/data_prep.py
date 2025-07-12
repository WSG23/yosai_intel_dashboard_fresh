from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

__all__ = ["prepare_security_data"]


def prepare_security_data(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """Prepare and clean data for security analysis."""
    logger = logger or logging.getLogger(__name__)
    # Use a shallow copy to preserve memory while ensuring the original
    # DataFrame remains unchanged
    df_clean = df.copy(deep=False)

    # Handle Unicode issues
    from security.unicode_security_handler import UnicodeSecurityHandler

    string_columns = df_clean.select_dtypes(include=["object"]).columns
    for col in string_columns:
        df_clean[col] = df_clean[col].astype(str).apply(
            UnicodeSecurityHandler.sanitize_unicode_input
        )

    # Ensure required columns exist
    required_cols = ["timestamp", "person_id", "door_id", "access_result"]
    missing_cols = [col for col in required_cols if col not in df_clean.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Convert timestamp
    if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
        df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])

    # Add derived features
    df_clean["hour"] = df_clean["timestamp"].dt.hour
    df_clean["day_of_week"] = df_clean["timestamp"].dt.dayofweek
    df_clean["is_weekend"] = df_clean["day_of_week"].isin([5, 6])
    df_clean["is_after_hours"] = df_clean["hour"].isin(list(range(0, 6)) + list(range(22, 24)))
    df_clean["access_granted"] = (df_clean["access_result"] == "Granted").astype(int)

    return df_clean
