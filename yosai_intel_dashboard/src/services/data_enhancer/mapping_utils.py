"""Utility functions for column matching and AI suggestions."""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import pandas as pd


def _fuzzy_match_columns(
    available_columns: Sequence[str],
    required_columns: Sequence[str],
) -> Dict[str, str]:
    """Return fuzzy matches for required columns."""
    suggestions: Dict[str, str] = {}
    mapping_patterns = {
        "person_id": [
            "person id",
            "userid",
            "user id",
            "user",
            "employee",
            "badge",
            "card",
            "person",
            "emp",
            "employee_id",
            "badge_id",
            "card_id",
        ],
        "door_id": [
            "device name",
            "devicename",
            "device_name",
            "door",
            "reader",
            "device",
            "access_point",
            "gate",
            "entry",
            "door_name",
            "reader_id",
            "access_device",
        ],
        "access_result": [
            "access result",
            "accessresult",
            "access_result",
            "result",
            "status",
            "outcome",
            "decision",
            "success",
            "granted",
            "denied",
            "access_status",
        ],
        "timestamp": [
            "timestamp",
            "time",
            "datetime",
            "date",
            "when",
            "occurred",
            "event_time",
            "access_time",
            "date_time",
            "event_date",
        ],
    }

    available_lower = {col.lower(): col for col in available_columns}
    for required_col, patterns in mapping_patterns.items():
        best_match = None
        for pattern in patterns:
            if pattern.lower() in available_lower:
                best_match = available_lower[pattern.lower()]
                break
        if not best_match:
            for pattern in patterns:
                for available_col_lower, original_col in available_lower.items():
                    if pattern in available_col_lower or available_col_lower in pattern:
                        best_match = original_col
                        break
                if best_match:
                    break
        if best_match:
            suggestions[required_col] = best_match
    return suggestions


def apply_fuzzy_column_matching(
    df: pd.DataFrame, required_columns: Sequence[str]
) -> Tuple[pd.DataFrame, Dict[str, str]]:
    """Rename columns in ``df`` based on fuzzy matching."""
    matches = _fuzzy_match_columns(list(df.columns), required_columns)
    renamed = df.rename(columns={v: k for k, v in matches.items()})
    return renamed, matches


def apply_manual_mapping(
    df: pd.DataFrame, column_mapping: Dict[str, str]
) -> pd.DataFrame:
    """Rename DataFrame columns using an explicit mapping."""
    missing_source_cols = [
        source for source in column_mapping.values() if source not in df.columns
    ]
    if missing_source_cols:
        raise ValueError(f"Source columns not found: {missing_source_cols}")
    return df.rename(columns={v: k for k, v in column_mapping.items()})


def get_mapping_suggestions(df: pd.DataFrame) -> Dict[str, Any]:
    """Return suggested column mappings for ``df``."""
    required_columns = ["person_id", "door_id", "access_result", "timestamp"]
    fuzzy_matches = _fuzzy_match_columns(list(df.columns), required_columns)
    return {
        "available_columns": list(df.columns),
        "required_columns": required_columns,
        "suggested_mappings": fuzzy_matches,
        "missing_mappings": [
            col for col in required_columns if col not in fuzzy_matches
        ],
    }


def get_ai_column_suggestions(columns: Sequence[str]) -> Dict[str, Dict[str, Any]]:
    """Provide simple heuristic column suggestions."""
    suggestions: Dict[str, Dict[str, Any]] = {}
    for column in columns:
        column_lower = column.lower()
        suggestion = {"field": "", "confidence": 0.0}
        if any(
            keyword in column_lower
            for keyword in ["person", "user", "employee", "name"]
        ):
            suggestion = {"field": "person_id", "confidence": 0.7}
        elif any(
            keyword in column_lower
            for keyword in ["door", "location", "device", "room"]
        ):
            suggestion = {"field": "door_id", "confidence": 0.7}
        elif any(keyword in column_lower for keyword in ["time", "date", "stamp"]):
            suggestion = {"field": "timestamp", "confidence": 0.8}
        elif any(keyword in column_lower for keyword in ["result", "status", "access"]):
            suggestion = {"field": "access_result", "confidence": 0.7}
        elif any(keyword in column_lower for keyword in ["token", "badge", "card"]):
            suggestion = {"field": "token_id", "confidence": 0.6}
        suggestions[column] = suggestion
    return suggestions


__all__ = [
    "apply_fuzzy_column_matching",
    "get_ai_column_suggestions",
    "apply_manual_mapping",
    "get_mapping_suggestions",
]
