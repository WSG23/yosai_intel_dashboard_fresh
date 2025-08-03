"""Metric repository abstractions and in-memory implementation."""
from __future__ import annotations

from typing import Any, Dict, Protocol


class MetricsRepository(Protocol):
    """Persistence operations for metric data."""

    def get_performance_metrics(self) -> Dict[str, Any]: ...
    def get_drift_data(self) -> Dict[str, Any]: ...
    def get_feature_importances(self) -> Dict[str, Any]: ...

    def snapshot(self) -> Dict[str, Any]:
        """Return a combined metric snapshot."""
        return {
            "performance": self.get_performance_metrics(),
            "drift": self.get_drift_data(),
            "feature_importance": self.get_feature_importances(),
        }


class InMemoryMetricsRepository:
    """Simple in-memory storage for metric data."""

    def __init__(
        self,
        performance: Dict[str, Any] | None = None,
        drift: Dict[str, Any] | None = None,
        feature_importances: Dict[str, Any] | None = None,
    ) -> None:
        self._performance = performance or {"throughput": 100, "latency_ms": 50}
        self._drift = drift or {"prediction_drift": 0.02, "feature_drift": {"age": 0.01}}
        self._feature_importances = feature_importances or {"age": 0.3, "income": 0.2, "score": 0.1}

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self._performance

    def get_drift_data(self) -> Dict[str, Any]:
        return self._drift

    def get_feature_importances(self) -> Dict[str, Any]:
        return self._feature_importances

    def snapshot(self) -> Dict[str, Any]:
        return {
            "performance": self.get_performance_metrics(),
            "drift": self.get_drift_data(),
            "feature_importance": self.get_feature_importances(),
        }


__all__ = ["MetricsRepository", "InMemoryMetricsRepository"]
