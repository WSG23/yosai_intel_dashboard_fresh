"""Metric repository abstractions and in-memory implementation."""
from __future__ import annotations

from typing import Any, Dict, Callable, TYPE_CHECKING
from cachetools import TTLCache
from threading import RLock
import warnings

from src.common.base import BaseComponent

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.src.core.protocols.metrics import MetricsRepositoryProtocol


class InMemoryMetricsRepository(BaseComponent):
    """Simple in-memory storage for metric data."""

    def __init__(
        self,
        performance: Dict[str, Any] | None = None,
        drift: Dict[str, Any] | None = None,
        feature_importances: Dict[str, Any] | None = None,
    ) -> None:
        BaseComponent.__init__(
            self,
            performance=performance
            or {"throughput": 100, "latency_ms": 50},
            drift=drift
            or {"prediction_drift": 0.02, "feature_drift": {"age": 0.01}},
            feature_importances=feature_importances
            or {"age": 0.3, "income": 0.2, "score": 0.1},
        )

    # Backward compatibility with previous attribute names
    @property
    def _performance(self) -> Dict[str, Any]:  # pragma: no cover - shim
        warnings.warn(
            "_performance is deprecated, use 'performance'", DeprecationWarning, stacklevel=2
        )
        return self.performance

    @property
    def _drift(self) -> Dict[str, Any]:  # pragma: no cover - shim
        warnings.warn(
            "_drift is deprecated, use 'drift'", DeprecationWarning, stacklevel=2
        )
        return self.drift

    @property
    def _feature_importances(self) -> Dict[str, Any]:  # pragma: no cover - shim
        warnings.warn(
            "_feature_importances is deprecated, use 'feature_importances'",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.feature_importances

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self.performance

    def get_drift_data(self) -> Dict[str, Any]:
        return self.drift

    def get_feature_importances(self) -> Dict[str, Any]:
        return self.feature_importances

    def snapshot(self) -> Dict[str, Any]:
        return {
            "performance": self.get_performance_metrics(),
            "drift": self.get_drift_data(),
            "feature_importance": self.get_feature_importances(),
        }


class CachedMetricsRepository(BaseComponent):
    """Wrap another repository and cache query results for a TTL."""

    def __init__(
        self, repo: MetricsRepositoryProtocol, ttl: int = 60, maxsize: int = 128
    ) -> None:
        BaseComponent.__init__(self, repo=repo, ttl=ttl, maxsize=maxsize)
        self._cache: TTLCache[str, Dict[str, Any]] = TTLCache(
            maxsize=maxsize, ttl=ttl
        )
        self._lock = RLock()

    # Backward compatibility for ``_repo`` attribute
    @property
    def _repo(self) -> MetricsRepositoryProtocol:  # pragma: no cover - shim
        warnings.warn("_repo is deprecated, use 'repo'", DeprecationWarning, stacklevel=2)
        return self.repo

    def _get_or_set(self, key: str, fn: Callable[[], Dict[str, Any]]) -> Dict[str, Any]:
        with self._lock:
            try:
                return self._cache[key]
            except KeyError:
                value = fn()
                self._cache[key] = value
                return value

    def get_performance_metrics(self) -> Dict[str, Any]:
        return self._get_or_set("performance", self.repo.get_performance_metrics)

    def get_drift_data(self) -> Dict[str, Any]:
        return self._get_or_set("drift", self.repo.get_drift_data)

    def get_feature_importances(self) -> Dict[str, Any]:
        return self._get_or_set("feature_importance", self.repo.get_feature_importances)

    def snapshot(self) -> Dict[str, Any]:
        return self._get_or_set(
            "snapshot",
            lambda: {
                "performance": self.repo.get_performance_metrics(),
                "drift": self.repo.get_drift_data(),
                "feature_importance": self.repo.get_feature_importances(),
            },
        )


__all__ = ["CachedMetricsRepository"]
