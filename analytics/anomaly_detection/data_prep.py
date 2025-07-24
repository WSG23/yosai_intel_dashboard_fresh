from __future__ import annotations

import logging
from typing import Optional

import pandas as pd

try:  # Avoid heavy package imports during tests
    from analytics.feature_extraction import extract_event_features
except Exception:  # pragma: no cover - fallback for dynamic loading
    import importlib.util
    from pathlib import Path

    _spec = importlib.util.spec_from_file_location(
        "analytics.feature_extraction",
        Path(__file__).resolve().parents[1] / "feature_extraction.py",
    )
    _module = importlib.util.module_from_spec(_spec)
    assert _spec and _spec.loader
    _spec.loader.exec_module(_module)
    extract_event_features = _module.extract_event_features

__all__ = ["prepare_anomaly_data"]


def prepare_anomaly_data(
    df: pd.DataFrame, logger: Optional[logging.Logger] = None
) -> pd.DataFrame:
    """Prepare and clean data for anomaly detection."""
    logger = logger or logging.getLogger(__name__)
    return extract_event_features(df, logger=logger)
