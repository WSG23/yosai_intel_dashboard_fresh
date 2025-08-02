from __future__ import annotations

"""Track model metrics, latency, and feature importance with drift detection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Sequence

import numpy as np
import pandas as pd

from yosai_intel_dashboard.src.services.monitoring.drift import detect_drift


@dataclass
class MetricSnapshot:
    """Persisted metrics for a batch of predictions."""

    accuracy: float
    precision: float
    recall: float
    f1: float
    latency: float
    throughput: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class ModelPerformanceTracker:
    """Collect model metrics and feature importance over time."""

    def __init__(self, *, drift_threshold: float = 0.1) -> None:
        self.drift_threshold = drift_threshold
        self.metrics_history: List[MetricSnapshot] = []
        self.feature_importance_history: List[Dict[str, float]] = []
        self.baseline_importance: Optional[Dict[str, float]] = None

    # ------------------------------------------------------------------
    def record_batch(
        self, y_true: Sequence[int], y_pred: Sequence[int], *, latency: float
    ) -> MetricSnapshot:
        """Record metrics for a batch of predictions."""
        y_true_arr = np.asarray(y_true)
        y_pred_arr = np.asarray(y_pred)
        if y_true_arr.size == 0:
            raise ValueError("y_true cannot be empty")
        tp = int(np.logical_and(y_true_arr == 1, y_pred_arr == 1).sum())
        tn = int(np.logical_and(y_true_arr == 0, y_pred_arr == 0).sum())
        fp = int(np.logical_and(y_true_arr == 0, y_pred_arr == 1).sum())
        fn = int(np.logical_and(y_true_arr == 1, y_pred_arr == 0).sum())

        precision = tp / (tp + fp) if (tp + fp) else 0.0
        recall = tp / (tp + fn) if (tp + fn) else 0.0
        accuracy = (tp + tn) / y_true_arr.size
        f1 = (
            2 * precision * recall / (precision + recall)
            if (precision + recall)
            else 0.0
        )
        throughput = y_pred_arr.size / latency if latency > 0 else 0.0

        snapshot = MetricSnapshot(
            accuracy=accuracy,
            precision=precision,
            recall=recall,
            f1=f1,
            latency=latency,
            throughput=throughput,
        )
        self.metrics_history.append(snapshot)
        return snapshot

    # ------------------------------------------------------------------
    def calculate_drift(
        self, baseline: pd.DataFrame, current: pd.DataFrame
    ) -> Dict[str, Dict[str, float]]:
        """Return drift metrics for ``current`` compared to ``baseline``."""
        return detect_drift(baseline, current)

    # ------------------------------------------------------------------
    def update_feature_importance(self, importances: Dict[str, float]) -> bool:
        """Persist feature importances and detect drift from the baseline."""
        self.feature_importance_history.append(importances.copy())
        if self.baseline_importance is None:
            self.baseline_importance = importances.copy()
            return False
        for feature, base_value in self.baseline_importance.items():
            current_value = importances.get(feature, 0.0)
            if base_value == 0.0:
                diff = abs(current_value - base_value)
            else:
                diff = abs(current_value - base_value) / base_value
            if diff > self.drift_threshold:
                return True
        return False


__all__ = ["ModelPerformanceTracker", "MetricSnapshot"]
