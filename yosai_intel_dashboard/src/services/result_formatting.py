import logging
from typing import Any, Dict, List

import pandas as pd


def ensure_datetime_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Return a copy of ``df`` with any datetime-like columns parsed."""

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
    """Safely perform a datetime ``operation`` on ``df[column]``."""

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


logger = logging.getLogger(__name__)


def prepare_regular_result(df: pd.DataFrame) -> Dict[str, Any]:
    """Create the base result structure for regular analysis."""
    return {
        "total_events": len(df),
        "columns": list(df.columns),
        "analysis_type": "regular",
        "processing_summary": {
            "total_input_rows": len(df),
            "rows_processed": len(df),
            "chunking_used": False,
        },
    }


def calculate_basic_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate basic statistics safely."""
    stats = {
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "memory_usage_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
    }

    key_columns = ["person_id", "door_id", "badge_id", "user_id", "access_result"]

    for col in key_columns:
        if col in df.columns:
            stats[f"unique_{col}"] = df[col].nunique()
            stats[f"total_{col}"] = df[col].count()

    if "access_result" in df.columns:
        stats["access_distribution"] = df["access_result"].value_counts().to_dict()

    return stats


def calculate_user_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate user-related statistics."""
    user_stats: Dict[str, Any] = {}
    user_col = None
    for col in ["person_id", "user_id", "employee_id"]:
        if col in df.columns:
            user_col = col
            break

    if user_col:
        user_stats["active_users"] = df[user_col].nunique()
        user_stats["total_user_events"] = df[user_col].count()
        user_stats["top_users"] = df[user_col].value_counts().head(10).to_dict()
    else:
        user_stats["error"] = "No user identifier column found"

    return user_stats


def calculate_access_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate access-related statistics."""
    access_stats: Dict[str, Any] = {}

    if "access_result" in df.columns:
        access_counts = df["access_result"].value_counts()
        access_stats["access_results"] = access_counts.to_dict()

        total_events = len(df)
        access_stats["access_percentages"] = {
            result: (count / total_events) * 100
            for result, count in access_counts.items()
        }

    if "door_id" in df.columns:
        access_stats["active_doors"] = df["door_id"].nunique()
        access_stats["door_usage"] = df["door_id"].value_counts().head(10).to_dict()

    return access_stats


def calculate_temporal_stats_safe(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculate temporal statistics with safe datetime handling."""
    temporal_stats: Dict[str, Any] = {}

    timestamp_col = None
    for col in ["timestamp", "datetime", "date", "time"]:
        if col in df.columns:
            timestamp_col = col
            break

    if not timestamp_col:
        logger.warning("No timestamp column found for temporal analysis")
        return {"error": "No timestamp column found"}

    try:
        if df[timestamp_col].dtype == "object":
            df[timestamp_col] = pd.to_datetime(df[timestamp_col], errors="coerce")

        dates = safe_datetime_operation(df, timestamp_col, "date")
        hours = safe_datetime_operation(df, timestamp_col, "hour")
        weekdays = safe_datetime_operation(df, timestamp_col, "weekday")

        if dates is not None:
            temporal_stats["date_range"] = {
                "start": str(dates.min()),
                "end": str(dates.max()),
                "total_days": (dates.max() - dates.min()).days,
            }

        if hours is not None:
            temporal_stats["hourly_distribution"] = hours.value_counts().to_dict()

        if weekdays is not None:
            temporal_stats["weekday_distribution"] = weekdays.value_counts().to_dict()

        temporal_stats["total_events"] = len(df)

    except Exception as e:  # pragma: no cover - unexpected
        logger.error(f"Error in temporal analysis: {e}")
        temporal_stats["error"] = str(e)

    return temporal_stats


def apply_regular_analysis(
    df: pd.DataFrame, analysis_types: List[str]
) -> Dict[str, Any]:
    """Run selected analysis sections for regular analysis."""
    result: Dict[str, Any] = {}

    if "basic" in analysis_types:
        result["basic_stats"] = calculate_basic_stats(df)

    if "temporal" in analysis_types or "time" in analysis_types:
        result["temporal_analysis"] = calculate_temporal_stats_safe(df)

    if "user" in analysis_types:
        result["user_analysis"] = calculate_user_stats(df)

    if "access" in analysis_types:
        result["access_analysis"] = calculate_access_stats(df)

    return result


def regular_analysis(df: pd.DataFrame, analysis_types: List[str]) -> Dict[str, Any]:
    """Perform regular analysis for smaller DataFrames."""
    logger.info(f"\U0001f4ca Starting regular analysis for {len(df):,} rows")

    df = ensure_datetime_columns(df)

    result = prepare_regular_result(df)
    result.update(apply_regular_analysis(df, analysis_types))

    logger.info(f"✅ Regular analysis completed for {len(df):,} rows")
    return result


__all__ = [
    "prepare_regular_result",
    "apply_regular_analysis",
    "calculate_temporal_stats_safe",
    "regular_analysis",
    "calculate_basic_stats",
    "calculate_user_stats",
    "calculate_access_stats",
]
