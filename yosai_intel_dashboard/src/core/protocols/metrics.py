from __future__ import annotations

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class MetricsRepositoryProtocol(Protocol):
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


__all__ = ["MetricsRepositoryProtocol"]
