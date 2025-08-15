"""Feature extraction utilities for analytics workflows."""

from __future__ import annotations

import pandas as pd

__all__ = [
    "extract_temporal_features",
    "extract_access_features",
    "extract_user_features",
    "extract_security_features",
    "extract_event_features",
]


def _ensure_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Validate input is a DataFrame and return a copy.

    Parameters
    ----------
    df:
        Input dataframe containing raw event data.

    Returns
    -------
    DataFrame
        A shallow copy of the input dataframe.

    Raises
    ------
    TypeError
        If *df* is not a pandas DataFrame.
    """

    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame")
    return df.copy()


def extract_temporal_features(df: pd.DataFrame) -> pd.DataFrame:
    """Extract temporal attributes from a ``timestamp`` column.

    Parameters
    ----------
    df:
        Dataframe with a ``timestamp`` column.

    Returns
    -------
    DataFrame
        A dataframe containing temporal feature columns ``hour``,
        ``day_of_week``, ``is_weekend`` and ``is_after_hours``.
    """

    frame = _ensure_dataframe(df)
    if "timestamp" not in frame:
        raise KeyError("'timestamp' column is required for temporal features")

    ts = pd.to_datetime(frame["timestamp"], errors="coerce")
    if ts.isna().any():
        raise ValueError("timestamp column contains non-datetime values")

    features = pd.DataFrame(index=frame.index)
    features["hour"] = ts.dt.hour
    features["day_of_week"] = ts.dt.dayofweek
    features["is_weekend"] = ts.dt.dayofweek.isin({5, 6})
    features["is_after_hours"] = ~ts.dt.hour.between(9, 17, inclusive="both")
    return features


def extract_access_features(df: pd.DataFrame) -> pd.DataFrame:
    """Derive features describing access outcomes.

    Parameters
    ----------
    df:
        Dataframe with an ``access_result`` column containing values such as
        ``"Granted"`` or ``"Denied"``.

    Returns
    -------
    DataFrame
        Dataframe with binary indicator columns for access patterns.
    """

    frame = _ensure_dataframe(df)
    if "access_result" not in frame:
        raise KeyError("'access_result' column is required for access features")

    result = frame["access_result"].astype(str).str.lower()
    features = pd.DataFrame(index=frame.index)
    features["access_granted"] = (result == "granted").astype(int)
    features["access_denied"] = (result == "denied").astype(int)
    return features


def extract_user_features(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate user behaviour statistics.

    Parameters
    ----------
    df:
        Dataframe with a ``person_id`` column.

    Returns
    -------
    DataFrame
        Dataframe containing ``user_event_count`` per event.
    """

    frame = _ensure_dataframe(df)
    if "person_id" not in frame:
        raise KeyError("'person_id' column is required for user features")

    counts = frame.groupby("person_id")["person_id"].transform("size")
    return pd.DataFrame({"user_event_count": counts}, index=frame.index)


def extract_security_features(df: pd.DataFrame) -> pd.DataFrame:
    """Compute security related statistics such as per-door counts.

    Parameters
    ----------
    df:
        Dataframe with a ``door_id`` column.

    Returns
    -------
    DataFrame
        Dataframe containing ``door_event_count`` per event.
    """

    frame = _ensure_dataframe(df)
    if "door_id" not in frame:
        raise KeyError("'door_id' column is required for security features")

    counts = frame.groupby("door_id")["door_id"].transform("size")
    return pd.DataFrame({"door_event_count": counts}, index=frame.index)


def extract_event_features(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience wrapper combining all feature extractors.

    Parameters
    ----------
    df:
        Raw event dataframe.

    Returns
    -------
    DataFrame
        The original dataframe augmented with derived feature columns.
    """

    frame = _ensure_dataframe(df)

    temporal = extract_temporal_features(frame)
    access = extract_access_features(frame)
    user = extract_user_features(frame)
    security = extract_security_features(frame)

    combined = pd.concat(
        [frame.reset_index(drop=True), temporal, access, user, security],
        axis=1,
    )
    return combined
