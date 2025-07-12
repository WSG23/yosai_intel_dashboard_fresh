"""Helper utilities used across analytics modules."""

from __future__ import annotations

import logging
from typing import Any

import pandas as pd

logger = logging.getLogger(__name__)


def ensure_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with any datetime-like columns parsed."""
    # Shallow copy so datetime parsing does not mutate the original
    df = df.copy(deep=False)
    timestamp_columns = [
        "timestamp",
        "datetime",
        "date",
        "time",
        "created_at",
        "updated_at",
    ]
    for col in df.columns:
        if (
            col.lower() in timestamp_columns
            or "time" in col.lower()
            or "date" in col.lower()
        ):
            if df[col].dtype == "object":
                try:
                    logger.info("Converting column '%s' to datetime", col)
                    df[col] = pd.to_datetime(df[col], errors="coerce")
                    logger.info("✅ Successfully converted '%s' to datetime", col)
                except Exception as exc:  # pragma: no cover - best effort
                    logger.warning("⚠️ Could not convert '%s' to datetime: %s", col, exc)
    return df


def safe_datetime_operation(df: pd.DataFrame, column: str, operation: str) -> Any:
    """Safely perform a datetime ``operation`` on ``df[column]``.

    ``None`` is returned when the column does not exist or the operation fails.
    Valid operations include ``date``, ``hour``, ``day``, ``month``, ``year``,
    ``dayofweek`` and ``weekday``.
    """
    if column not in df.columns:
        logger.warning("Column '%s' not found in DataFrame", column)
        return None

    if df[column].dtype == "object":
        logger.info("Converting '%s' to datetime for operation '%s'", column, operation)
        df[column] = pd.to_datetime(df[column], errors="coerce")

    try:
        if operation == "date":
            return df[column].dt.date
        if operation == "hour":
            return df[column].dt.hour
        if operation == "day":
            return df[column].dt.day
        if operation == "month":
            return df[column].dt.month
        if operation == "year":
            return df[column].dt.year
        if operation == "dayofweek":
            return df[column].dt.dayofweek
        if operation == "weekday":
            return df[column].dt.day_name()
        logger.warning("Unknown datetime operation: %s", operation)
    except Exception as exc:  # pragma: no cover - best effort
        logger.error(
            "Error performing datetime operation '%s' on column '%s': %s",
            operation,
            column,
            exc,
        )
    return None
