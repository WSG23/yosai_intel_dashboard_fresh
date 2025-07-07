from __future__ import annotations

from typing import Dict

import pandas as pd

# Mapping of known column headers in various languages to standard field names
COLUMN_NAME_MAP: Dict[str, str] = {
    "Timestamp": "timestamp",
    "Person ID": "person_id",
    "Token ID": "token_id",
    "Device name": "door_id",
    "Access result": "access_result",
    "タイムスタンプ": "timestamp",
    "ユーザーID": "person_id",
    "トークンID": "token_id",
    "ドア名": "door_id",
    "結果": "access_result",
}


def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Rename known column headers to canonical snake_case names."""
    mapping = {col: COLUMN_NAME_MAP[col] for col in df.columns if col in COLUMN_NAME_MAP}
    return df.rename(columns=mapping)


__all__ = ["standardize_column_names", "COLUMN_NAME_MAP"]
