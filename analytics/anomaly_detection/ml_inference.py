from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import DBSCAN
from sklearn.neural_network import MLPRegressor
from sklearn.preprocessing import StandardScaler

__all__ = ["detect_ml_anomalies"]


def detect_ml_anomalies(
    df: pd.DataFrame,
    sensitivity: float,
    isolation_forest: IsolationForest,
    dbscan_model: Optional[DBSCAN] = None,
    autoencoder_model: Optional[MLPRegressor] = None,
    dbscan_scaler: Optional[StandardScaler] = None,
    autoencoder_scaler: Optional[StandardScaler] = None,
    logger: Optional[logging.Logger] = None,
) -> List[Dict[str, Any]]:
    """Detect anomalies using an ensemble of ML models."""
    logger = logger or logging.getLogger(__name__)
    anomalies: List[Dict[str, Any]] = []
    try:
        features = ["hour", "day_of_week", "is_weekend", "is_after_hours", "access_granted"]
        feature_df = df[features].copy(deep=False)
        if len(feature_df) < 10:
            return anomalies

        scores: List[np.ndarray] = []

        # Isolation Forest score (normalized)
        isolation_forest.set_params(contamination=1 - sensitivity)
        iso_scores = -isolation_forest.fit(feature_df).decision_function(feature_df)
        iso_scores = (iso_scores - iso_scores.min()) / (iso_scores.ptp() + 1e-9)
        scores.append(iso_scores)

        # DBSCAN score if model provided
        if dbscan_model is not None:
            db_data = feature_df if dbscan_scaler is None else dbscan_scaler.transform(feature_df)
            db_labels = dbscan_model.fit_predict(db_data)
            db_scores = (db_labels == -1).astype(float)
            scores.append(db_scores)

        # Autoencoder reconstruction error if model provided
        if autoencoder_model is not None:
            ae_data = feature_df if autoencoder_scaler is None else autoencoder_scaler.transform(feature_df)
            ae_recon = autoencoder_model.predict(ae_data)
            if ae_recon.ndim == 1:
                ae_recon = ae_recon.reshape(-1, 1)
            ae_scores = np.mean((ae_data - ae_recon) ** 2, axis=1)
            ae_scores = (ae_scores - ae_scores.min()) / (ae_scores.ptp() + 1e-9)
            scores.append(ae_scores)

        aggregated_scores = np.mean(np.column_stack(scores), axis=1)
        threshold = np.quantile(aggregated_scores, sensitivity)
        anomaly_indices = np.where(aggregated_scores >= threshold)[0]

        for idx in anomaly_indices:
            original_row = df.iloc[idx]
            anomalies.append(
                {
                    "type": "ml_anomaly",
                    "details": {
                        "person_id": original_row["person_id"],
                        "door_id": original_row["door_id"],
                        "timestamp": original_row["timestamp"].isoformat(),
                        "features": feature_df.iloc[idx].to_dict(),
                    },
                    "severity": "medium",
                    "confidence": float(aggregated_scores[idx]),
                    "timestamp": datetime.now(),
                }
            )
    except Exception as exc:  # pragma: no cover - log and continue
        logger.warning("ML anomaly detection failed: %s", exc)
    return anomalies
