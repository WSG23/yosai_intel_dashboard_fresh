from __future__ import annotations

import pandas as pd
import logging
from typing import Optional

__all__ = ["prepare_anomaly_data"]


def prepare_anomaly_data(df: pd.DataFrame, logger: Optional[logging.Logger] = None) -> pd.DataFrame:
    """Prepare and clean data for anomaly detection."""
    logger = logger or logging.getLogger(__name__)
    df_clean = df.copy()

    from security.unicode_security_handler import UnicodeSecurityHandler

    string_columns = df_clean.select_dtypes(include=["object"]).columns
    for col in string_columns:
        df_clean[col] = df_clean[col].astype(str).apply(
            UnicodeSecurityHandler.sanitize_unicode_input
        )

    required_cols = ["timestamp", "person_id", "door_id", "access_result"]
    for col in required_cols:
        if col not in df_clean.columns:
            if col == "timestamp":
                df_clean[col] = pd.Timestamp.now()
            elif col in ["person_id", "door_id"]:
                df_clean[col] = f"unknown_{col}"
            elif col == "access_result":
                df_clean[col] = "Unknown"

    if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
        try:
            df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"])
        except Exception:
            df_clean["timestamp"] = pd.Timestamp.now()

    df_clean["hour"] = df_clean["timestamp"].dt.hour
    df_clean["day_of_week"] = df_clean["timestamp"].dt.dayofweek
    df_clean["is_weekend"] = df_clean["day_of_week"].isin([5, 6])
    df_clean["is_after_hours"] = df_clean["hour"].isin(list(range(0, 6)) + list(range(22, 24)))
    df_clean["access_granted"] = (df_clean["access_result"] == "Granted").astype(int)

    return df_clean
