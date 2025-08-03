"""Anomaly detection utilities using IsolationForest."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional, Tuple

import pandas as pd
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    """Detect unusual access patterns for users or IP addresses.

    The detector is trained on historical access events provided by
    ``AccessEventModel`` and uses :class:`~sklearn.ensemble.IsolationForest`
    to assign anomaly scores.
    """

    def __init__(
        self,
        access_model: Optional[Any] = None,
        contamination: float = 0.05,
        random_state: int = 42,
    ) -> None:
        self.access_model = access_model
        self.model = IsolationForest(
            contamination=contamination, random_state=random_state
        )
        self.is_trained = False
        self.logger = logging.getLogger(__name__)
        self.metrics: Dict[str, int] = {"total_events": 0, "anomalies": 0}
        self.user_counts: Dict[str, int] = {}
        self.ip_counts: Dict[str, int] = {}

    def _extract_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare numeric features from raw access event data."""
        if df is None or df.empty:
            return pd.DataFrame(columns=["user_count", "ip_count"])

        if "user_id" in df.columns:
            self.user_counts = df["user_id"].value_counts().to_dict()
            df["user_count"] = df["user_id"].map(self.user_counts)
        else:
            df["user_count"] = 0

        if "source_ip" in df.columns:
            self.ip_counts = df["source_ip"].value_counts().to_dict()
            df["ip_count"] = df["source_ip"].map(self.ip_counts)
        else:
            df["ip_count"] = 0

        return df[["user_count", "ip_count"]].fillna(0)

    def train(self) -> None:
        """Train the underlying model on historical access events."""
        if self.access_model is None:
            self.logger.warning(
                "No AccessEventModel available; anomaly detection disabled"
            )
            return

        df = self.access_model.get_data()
        features = self._extract_features(df)
        if not features.empty:
            self.model.fit(features)
            self.is_trained = True
        else:
            self.logger.warning("No data available to train anomaly detector")

    def score(
        self, user_id: Optional[str], source_ip: Optional[str]
    ) -> Tuple[float, bool]:
        """Return anomaly score and flag for a new event."""
        if not self.is_trained:
            self.train()
            if not self.is_trained:
                return 0.0, False

        user_count = self.user_counts.get(user_id, 0)
        ip_count = self.ip_counts.get(source_ip, 0)
        features = [[user_count, ip_count]]
        score = float(self.model.decision_function(features)[0])
        is_anomaly = score < 0 or user_count == 0 or ip_count == 0

        self.metrics["total_events"] += 1
        if is_anomaly:
            self.metrics["anomalies"] += 1

        return score, is_anomaly

    def get_metrics(self) -> Dict[str, int]:
        """Return aggregated anomaly detection metrics."""
        return dict(self.metrics)


__all__ = ["AnomalyDetector"]
