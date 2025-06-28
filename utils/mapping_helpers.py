"""Utility functions for mapping uploaded data columns."""

from typing import Dict
import pandas as pd

# Standard column mapping used across the project
STANDARD_COLUMN_MAPPING: Dict[str, str] = {
    "Timestamp": "timestamp",
    "Person ID": "person_id",
    "Token ID": "token_id",
    "Device name": "door_id",
    "Access result": "access_result",
}


def map_and_clean(df: pd.DataFrame) -> pd.DataFrame:
    """Rename columns using :data:`STANDARD_COLUMN_MAPPING` and clean fields."""
    df = df.rename(columns=STANDARD_COLUMN_MAPPING)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    for col in ("person_id", "door_id", "access_result"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df


__all__ = ["STANDARD_COLUMN_MAPPING", "map_and_clean"]
