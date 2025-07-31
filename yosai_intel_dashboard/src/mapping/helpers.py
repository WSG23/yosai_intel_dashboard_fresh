from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

STANDARD_COLUMN_MAPPING: Dict[str, str] = {
    "Timestamp": "timestamp",
    "Person ID": "person_id",
    "Token ID": "token_id",
    "Device name": "door_id",
    "Access result": "access_result",
}


def map_and_clean(
    df: pd.DataFrame, learned_mappings: Optional[Dict[str, str]] = None
) -> pd.DataFrame:
    mappings = STANDARD_COLUMN_MAPPING.copy()
    if learned_mappings:
        mappings.update(learned_mappings)

    df = df.rename(columns=mappings)

    if "timestamp" in df.columns:
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")

    for col in ("person_id", "door_id", "access_result"):
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    return df
