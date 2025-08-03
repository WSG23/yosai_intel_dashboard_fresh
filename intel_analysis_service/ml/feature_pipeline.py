"""Feature pipelines for context-aware models.

This module exposes utilities to merge several event streams into a single
feature DataFrame used by downstream models.  Each event stream is expected to
contain a ``timestamp`` column which will be used for alignment.
"""

from __future__ import annotations

from functools import reduce
from typing import Iterable

import pandas as pd


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure a DataFrame has a ``timestamp`` column and is sorted."""
    if "timestamp" not in df:
        raise KeyError("DataFrame must contain 'timestamp' column")
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.sort_values("timestamp")


def build_context_features(
    weather_events: pd.DataFrame,
    events: pd.DataFrame,
    transport_events: pd.DataFrame,
    social_signals: pd.DataFrame,
    infrastructure_events: pd.DataFrame,
) -> pd.DataFrame:
    """Combine heterogeneous event streams into a single feature set.

    Parameters
    ----------
    weather_events, events, transport_events, social_signals, infrastructure_events:
        DataFrames with a ``timestamp`` column.  The remaining columns represent
        features to be used for modeling.

    Returns
    -------
    pandas.DataFrame
        DataFrame indexed by timestamp containing the union of all features.  All
        missing values are filled with ``0``.
    """

    dataframes: Iterable[pd.DataFrame] = (
        weather_events,
        events,
        transport_events,
        social_signals,
        infrastructure_events,
    )

    normalized = [_normalize(df) for df in dataframes]

    # Perform an outer join across all data sources on timestamp.
    features = reduce(
        lambda left, right: pd.merge(left, right, on="timestamp", how="outer"),
        normalized,
    )

    features = features.sort_values("timestamp").fillna(0)
    return features
