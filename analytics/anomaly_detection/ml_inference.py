from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

__all__ = ["detect_ml_anomalies"]


def detect_ml_anomalies(
    df: pd.DataFrame,
    sensitivity: float,
    isolation_forest: IsolationForest,
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """Detect anomalies using an IsolationForest model."""
    logger = logger or logging.getLogger(__name__)
    anomalies: List[Dict[str, Any]] = []
    try:
        features = ['hour', 'day_of_week', 'is_weekend', 'is_after_hours', 'access_granted']
        feature_df = df[features].copy()
        if len(feature_df) < 10:
            return anomalies
        isolation_forest.set_params(contamination=1 - sensitivity)
        outliers = isolation_forest.fit_predict(feature_df)
        anomaly_indices = np.where(outliers == -1)[0]
        for idx in anomaly_indices:
            original_row = df.iloc[idx]
            anomalies.append({
                "type": "ml_anomaly",
                "details": {
                    "person_id": original_row["person_id"],
                    "door_id": original_row["door_id"],
                    "timestamp": original_row["timestamp"].isoformat(),
                    "features": feature_df.iloc[idx].to_dict(),
                },
                "severity": "medium",
                "confidence": 0.6,
                "timestamp": datetime.now(),
            })
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("ML anomaly detection failed: %s", exc)
    return anomalies
