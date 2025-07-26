from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

from validation.unicode_validator import UnicodeValidator

__all__ = ["extract_event_features"]


def extract_event_features(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """Add common derived features to an access events dataframe."""
    logger = logger or logging.getLogger(__name__)
    if df is None or len(df) == 0:
        return pd.DataFrame()

    df_clean = df.copy(deep=False)

    # Sanitize string columns
    try:
        validator = UnicodeValidator()
        df_clean = validator.validate_dataframe(df_clean)

    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("Unicode sanitization failed: %s", exc)

    # Ensure required columns exist
    required_cols = ["timestamp", "person_id", "door_id", "access_result"]
    for col in required_cols:
        if col not in df_clean.columns:
            if col == "timestamp":
                df_clean[col] = pd.Timestamp.now()
            else:
                df_clean[col] = f"unknown_{col}"

    if not pd.api.types.is_datetime64_any_dtype(df_clean["timestamp"]):
        df_clean["timestamp"] = pd.to_datetime(df_clean["timestamp"], errors="coerce")
        df_clean["timestamp"].fillna(pd.Timestamp.now(), inplace=True)

    df_clean["hour"] = df_clean["timestamp"].dt.hour
    df_clean["day_of_week"] = df_clean["timestamp"].dt.dayofweek
    df_clean["is_weekend"] = df_clean["day_of_week"].isin([5, 6])
    df_clean["is_after_hours"] = df_clean["hour"].isin(list(range(0, 6)) + list(range(22, 24)))
    df_clean["access_granted"] = (df_clean["access_result"] == "Granted").astype(int)

    # Counts per user and door
    user_counts = df_clean["person_id"].value_counts()
    df_clean["user_event_count"] = df_clean["person_id"].map(user_counts).astype(int)
    door_counts = df_clean["door_id"].value_counts()
    df_clean["door_event_count"] = df_clean["door_id"].map(door_counts).astype(int)

    return df_clean
