"""Utility helpers for processing uploaded files during analytics."""

from __future__ import annotations

import logging
from collections import Counter
from datetime import datetime
from typing import Any, Dict, Iterable, Tuple

from config.constants import DEFAULT_CHUNK_SIZE

import pandas as pd

logger = logging.getLogger(__name__)


def stream_uploaded_file(data_loader, source: Any, chunksize: int = DEFAULT_CHUNK_SIZE):
    """Yield cleaned ``DataFrame`` chunks from ``source`` using ``data_loader``."""
    yield from data_loader.stream_file(source, chunksize)


def update_counts(
    df: pd.DataFrame, user_counts: Counter[str], door_counts: Counter[str]
) -> None:
    """Update ``user_counts`` and ``door_counts`` using values from ``df``."""
    if "person_id" in df.columns:
        user_counts.update(df["person_id"].dropna().astype(str))
    if "door_id" in df.columns:
        door_counts.update(df["door_id"].dropna().astype(str))


def update_timestamp_range(
    df: pd.DataFrame,
    min_ts: pd.Timestamp | None,
    max_ts: pd.Timestamp | None,
) -> Tuple[pd.Timestamp | None, pd.Timestamp | None]:
    """Return updated ``min_ts`` and ``max_ts`` based on ``df``."""
    if "timestamp" in df.columns:
        ts = pd.to_datetime(df["timestamp"], errors="coerce").dropna()
        if not ts.empty:
            cur_min = ts.min()
            cur_max = ts.max()
            if min_ts is None or cur_min < min_ts:
                min_ts = cur_min
            if max_ts is None or cur_max > max_ts:
                max_ts = cur_max
    return min_ts, max_ts


def aggregate_counts(
    frames: Iterable[pd.DataFrame],
    user_counts: Counter[str],
    door_counts: Counter[str],
    min_ts: pd.Timestamp | None,
    max_ts: pd.Timestamp | None,
) -> Tuple[int, pd.Timestamp | None, pd.Timestamp | None]:
    """Aggregate counters and timestamps from an iterable of ``frames``."""
    total = 0
    for df in frames:
        total += len(df)
        update_counts(df, user_counts, door_counts)
        min_ts, max_ts = update_timestamp_range(df, min_ts, max_ts)
    return total, min_ts, max_ts


def calculate_date_range(
    min_ts: pd.Timestamp | None, max_ts: pd.Timestamp | None
) -> Dict[str, str]:
    """Return a dictionary representing the processed date range."""
    if min_ts is not None and max_ts is not None:
        return {
            "start": min_ts.strftime("%Y-%m-%d"),
            "end": max_ts.strftime("%Y-%m-%d"),
        }
    return {"start": "Unknown", "end": "Unknown"}


def build_result(
    total_events: int,
    user_counts: Counter[str],
    door_counts: Counter[str],
    date_range: Dict[str, str],
    processing_info: Dict[str, Any],
) -> Dict[str, Any]:
    """Construct the final analytics result dictionary."""
    active_users = len(user_counts)
    active_doors = len(door_counts)
    return {
        "status": "success",
        "total_events": total_events,
        "active_users": active_users,
        "active_doors": active_doors,
        "unique_users": active_users,
        "unique_doors": active_doors,
        "data_source": "uploaded",
        "date_range": date_range,
        "top_users": [
            {"user_id": u, "count": int(c)} for u, c in user_counts.most_common(10)
        ],
        "top_doors": [
            {"door_id": d, "count": int(c)} for d, c in door_counts.most_common(10)
        ],
        "timestamp": datetime.now().isoformat(),
        "processing_info": processing_info,
    }
