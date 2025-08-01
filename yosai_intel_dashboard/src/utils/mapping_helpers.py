"""Utility functions for mapping uploaded data columns."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Dict, Optional

import pandas as pd

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from yosai_intel_dashboard.src.mapping.models import ColumnRules
else:  # pragma: no cover - fallback at runtime
    ColumnRules = Any  # type: ignore[misc]

# Standard column mapping used across the project
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
    """Rename columns using provided mappings and clean fields.

    Parameters
    ----------
    df:
        DataFrame to clean.
    learned_mappings:
        Optional user or AI learned column mappings. These take precedence over
        :data:`STANDARD_COLUMN_MAPPING`.
    """

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


def standardize_column_names(
    df: pd.DataFrame, rules: ColumnRules | None = None
) -> pd.DataFrame:
    """Return a new DataFrame with normalized column names."""

    if rules is None:
        from yosai_intel_dashboard.src.mapping.models import load_rules

        rules = load_rules()
    df_out = df.copy()

    mappings: Dict[str, list[str]] = {**rules.english}
    for key, vals in rules.japanese.items():
        mappings.setdefault(key, []).extend(vals)

    reverse: Dict[str, str] = {}
    for canon, aliases in mappings.items():
        reverse[canon.lower()] = canon
        for alias in aliases:
            reverse[str(alias).lower()] = canon

    renamed: Dict[str, str] = {}
    for col in df_out.columns:
        target = reverse.get(str(col).lower())
        if target:
            renamed[col] = target
    if renamed:
        df_out = df_out.rename(columns=renamed)

    df_out.columns = [
        re.sub(r"\W+", "_", str(c)).strip("_").lower() for c in df_out.columns
    ]
    return df_out


__all__ = [
    "STANDARD_COLUMN_MAPPING",
    "map_and_clean",
    "standardize_column_names",
]
