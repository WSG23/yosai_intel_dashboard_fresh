"""Metric repository abstractions and in-memory implementation (see ADR 0004)."""

from __future__ import annotations

from threading import RLock
from typing import Any, Callable, Dict, Protocol

from cachetools import TTLCache


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
        self._drift = drift or {
            "prediction_drift": 0.02,
            "feature_drift": {"age": 0.01},
        }
        self._feature_importances = feature_importances or {
            "age": 0.3,
            "income": 0.2,
            "score": 0.1,
        }

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


class CachedMetricsRepository:
    """Wrap another repository and cache query results for a TTL."""

    def __init__(
        self, repo: MetricsRepository, ttl: int = 60, maxsize: int = 128
    ) -> None:
        self._repo = repo
        self._cache: TTLCache[str, Dict[str, Any]] = TTLCache(maxsize=maxsize, ttl=ttl)
        self._lock = RLock()

    def _get_or_set(self, key: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        with self._lock:
            try:
                return self._cache[key]
            except KeyError:
                value = fn()
                self._cache[key] = value
                return value

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self._get_or_set("performance", self._repo.get_performance_metrics)

    def get_drift_data(self) -> Dict[str, Any]:
        return self._get_or_set("drift", self._repo.get_drift_data)

    def get_feature_importances(self) -> Dict[str, Any]:
        return self._get_or_set(
            "feature_importance", self._repo.get_feature_importances
        )

    def snapshot(self) -> Dict[str, Any]:
        return self._get_or_set(
            "snapshot",
            lambda: {
                "performance": self._repo.get_performance_metrics(),
                "drift": self._repo.get_drift_data(),
                "feature_importance": self._repo.get_feature_importances(),
            },
        )


__all__ = ["MetricsRepository", "InMemoryMetricsRepository", "CachedMetricsRepository"]
