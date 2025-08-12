from __future__ import annotations

"""Shared preprocessing contract for event-based models.

This module exposes a single helper :func:`preprocess_events` which applies
all agreed upon feature engineering steps.  Both training code and inference
services should rely on this function to ensure the same transformations are
used across the project.
"""

from typing import Any
import pandas as pd

from analytics import feature_extraction


def preprocess_events(df: pd.DataFrame) -> pd.DataFrame:
    """Return the canonical feature set for raw event data.

    Parameters
    ----------
    df:
        Raw event dataframe containing columns such as ``timestamp`` and
        ``access_result``.

    Returns
    -------
    DataFrame
        The input dataframe augmented with engineered feature columns.
    """

    return feature_extraction.extract_event_features(df)


__all__ = ["preprocess_events"]
