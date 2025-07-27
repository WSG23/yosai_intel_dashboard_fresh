from __future__ import annotations

"""Utilities for tracking ML model performance."""

from dataclasses import dataclass
from typing import Any, Optional

import logging
from datetime import datetime

from core.performance import MetricType, get_performance_monitor
from monitoring.prometheus.model_metrics import update_model_metrics


@dataclass
class ModelMetrics:
    """Container for common model evaluation metrics."""

    accuracy: float
    precision: float
    recall: float


class ModelPerformanceMonitor:
    """Log model metrics and detect simple performance drift."""

    def __init__(
        self,
        baseline: Optional[ModelMetrics] = None,
        drift_threshold: float = 0.05,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        self.baseline = baseline
        self.drift_threshold = drift_threshold
        self.logger = logger or logging.getLogger("model_predictions")

    # ------------------------------------------------------------------
    def log_metrics(self, metrics: ModelMetrics) -> None:
        """Record metrics using :class:`PerformanceMonitor`."""
        monitor = get_performance_monitor()
        monitor.record_metric(
            "model.accuracy", metrics.accuracy, MetricType.FILE_PROCESSING
        )
        monitor.record_metric(
            "model.precision", metrics.precision, MetricType.FILE_PROCESSING
        )
        monitor.record_metric(
            "model.recall", metrics.recall, MetricType.FILE_PROCESSING
        )
        update_model_metrics(metrics)

    # ------------------------------------------------------------------
    def log_prediction(
        self,
        input_hash: str,
        prediction: Any,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """Emit a prediction event via the configured logger."""
        ts = timestamp or datetime.utcnow()
        self.logger.info(
            "model_prediction",
            extra={
                "input_hash": input_hash,
                "prediction": prediction,
                "timestamp": ts.isoformat(),
            },
        )

    # ------------------------------------------------------------------
    def detect_drift(self, metrics: ModelMetrics) -> bool:
        """Return ``True`` if metrics deviate from the baseline by ``drift_threshold``."""
        if not self.baseline:
            return False
        return any(
            abs(getattr(metrics, field) - getattr(self.baseline, field))
            > self.drift_threshold
            for field in ("accuracy", "precision", "recall")
        )


_model_performance_monitor: Optional[ModelPerformanceMonitor] = None


def get_model_performance_monitor() -> ModelPerformanceMonitor:
    """Return the global :class:`ModelPerformanceMonitor` instance."""
    global _model_performance_monitor
    if _model_performance_monitor is None:
        _model_performance_monitor = ModelPerformanceMonitor()
    return _model_performance_monitor


__all__ = [
    "ModelMetrics",
    "ModelPerformanceMonitor",
    "get_model_performance_monitor",
]
