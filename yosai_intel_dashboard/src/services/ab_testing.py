"""Simple A/B testing wrapper for ML models."""

from __future__ import annotations

import json
import logging
import random
from pathlib import Path
from time import perf_counter
from typing import Any, Dict, Iterable, Optional

import joblib
from scipy.stats import chi2_contingency

try:  # pragma: no cover - optional dependency
    from prometheus_client import Counter, Histogram  # type: ignore
except Exception:  # pragma: no cover - fallback when prometheus not installed
    Counter = Histogram = None  # type: ignore

if Counter:
    _PROM_COUNTS = Counter(
        "ab_predictions_total",
        "Total A/B test predictions",
        ["model", "version"],
        registry=None,
    )
    _PROM_SUCCESS = Counter(
        "ab_prediction_success_total",
        "Successful A/B test predictions",
        ["model", "version"],
        registry=None,
    )
    _PROM_LATENCY = Histogram(
        "ab_prediction_latency_seconds",
        "Latency of A/B test predictions",
        ["model", "version"],
        registry=None,
    )
else:  # pragma: no cover - metrics disabled
    _PROM_COUNTS = _PROM_SUCCESS = _PROM_LATENCY = None

try:  # pragma: no cover - ensure joblib can pickle local objects
    import cloudpickle  # type: ignore

    def _joblib_dump(obj, filename, *args, **kwargs):
        with open(filename, "wb") as fh:
            cloudpickle.dump(obj, fh)

    joblib.dump = _joblib_dump  # type: ignore
except Exception:  # pragma: no cover - cloudpickle may be unavailable
    pass

from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - type checking only
    from yosai_intel_dashboard.models.ml import ModelRegistry


class ModelABTester:
    """Route predictions across model versions based on configured weights."""

    def __init__(
        self,
        model_name: str,
        registry: ModelRegistry,
        *,
        weights: Optional[Dict[str, float]] = None,
        weights_file: str = "ab_weights.json",
        model_dir: str = "ab_models",
        metrics_file: str | None = None,
        significance_level: float = 0.05,
        min_samples: int = 30,
    ) -> None:
        self.model_name = model_name
        self.registry = registry
        self.weights_file = Path(weights_file)
        self.metrics_file = (
            Path(metrics_file)
            if metrics_file is not None
            else self.weights_file.with_name("ab_metrics.json")
        )
        self.model_dir = Path(model_dir)
        self.logger = logging.getLogger(__name__)
        self.weights: Dict[str, float] = weights or self._load_weights()
        self.metrics: Dict[str, Dict[str, float]] = self._load_metrics()
        self.models: Dict[str, Any] = {}
        self.significance_level = significance_level
        self.min_samples = min_samples
        if Counter:
            self._prom_counts = _PROM_COUNTS
            self._prom_success = _PROM_SUCCESS
            self._prom_latency = _PROM_LATENCY
        if self.weights:
            self._load_models()

    # ------------------------------------------------------------------
    def _load_weights(self) -> Dict[str, float]:
        if self.weights_file.exists():
            try:
                with self.weights_file.open() as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return {str(k): float(v) for k, v in data.items()}
            except Exception as exc:  # pragma: no cover - best effort
                self.logger.warning("Failed to load weights: %s", exc)
        return {}

    def _save_weights(self) -> None:
        try:
            with self.weights_file.open("w") as fh:
                json.dump(self.weights, fh)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.error("Failed to save weights: %s", exc)

    def _load_metrics(self) -> Dict[str, Dict[str, float]]:
        if self.metrics_file.exists():
            try:
                with self.metrics_file.open() as fh:
                    data = json.load(fh)
                if isinstance(data, dict):
                    return {
                        str(k): {
                            "count": float(v.get("count", 0)),
                            "success": float(v.get("success", 0)),
                            "latency_sum": float(v.get("latency_sum", 0.0)),
                        }
                        for k, v in data.items()
                    }
            except Exception as exc:  # pragma: no cover - best effort
                self.logger.warning("Failed to load metrics: %s", exc)
        return {}

    def _save_metrics(self) -> None:
        try:
            with self.metrics_file.open("w") as fh:
                json.dump(self.metrics, fh)
        except Exception as exc:  # pragma: no cover - best effort
            self.logger.error("Failed to save metrics: %s", exc)

    def _load_models(self) -> None:
        self.models.clear()
        for version in self.weights:
            record = self.registry.get_model(self.model_name, version=version)
            if record is None:
                self.logger.warning(
                    "Model %s version %s not found in registry",
                    self.model_name,
                    version,
                )
                continue
            self.model_dir.mkdir(parents=True, exist_ok=True)
            local_path = self.model_dir / f"{self.model_name}_{version}.bin"
            if not local_path.exists():
                try:
                    self.registry.download_artifact(record.storage_uri, str(local_path))
                except Exception as exc:  # pragma: no cover - network failures
                    self.logger.error(
                        "Failed to download model %s:%s - %s",
                        self.model_name,
                        version,
                        exc,
                    )
                    continue
            try:
                model = joblib.load(local_path)
                self.models[version] = model
            except Exception as exc:  # pragma: no cover - invalid files
                self.logger.error(
                    "Failed to load model artifact %s - %s", local_path, exc
                )

    # ------------------------------------------------------------------
    def set_weights(self, weights: Dict[str, float]) -> None:
        """Update traffic weights and reload models."""
        self.weights = {str(k): float(v) for k, v in weights.items()}
        self._save_weights()
        self._load_models()

    # ------------------------------------------------------------------
    def _choose_version(self) -> str:
        versions = list(self.weights.keys())
        probs = [self.weights[v] for v in versions]
        total = sum(probs)
        if total <= 0:
            raise RuntimeError("Invalid weights: sum must be > 0")
        return random.choices(versions, weights=probs, k=1)[0]

    def _record_metrics(
        self, version: str, success: Optional[bool], latency: float
    ) -> None:
        stats = self.metrics.setdefault(
            version, {"count": 0.0, "success": 0.0, "latency_sum": 0.0}
        )
        stats["count"] += 1
        stats["latency_sum"] += float(latency)
        if success is not None:
            stats["success"] += int(success)
            if Counter:
                self._prom_success.labels(self.model_name, version).inc(int(success))
        if Counter:
            self._prom_counts.labels(self.model_name, version).inc()
            self._prom_latency.labels(self.model_name, version).observe(latency)
        self._save_metrics()

    def _evaluate_promotion(self) -> None:
        baseline_record = self.registry.get_model(
            self.model_name, active_only=True
        )
        if baseline_record is None:
            return
        baseline_version = str(baseline_record.version)
        base_stats = self.metrics.get(baseline_version)
        if not base_stats or base_stats["count"] < self.min_samples:
            return
        base_success = base_stats["success"]
        base_fail = base_stats["count"] - base_success
        for version, stats in self.metrics.items():
            if version == baseline_version or stats["count"] < self.min_samples:
                continue
            var_success = stats["success"]
            var_fail = stats["count"] - var_success
            table = [[var_success, var_fail], [base_success, base_fail]]
            try:
                chi2, p, _, _ = chi2_contingency(table)
            except Exception:  # pragma: no cover - invalid data
                continue
            base_rate = base_success / base_stats["count"]
            var_rate = var_success / stats["count"]
            if p < self.significance_level and var_rate > base_rate:
                self.registry.set_active_version(self.model_name, version)
                self.set_weights({version: 1.0})
                self.logger.info(
                    "ab_test_promotion",
                    extra={"winner": version, "p_value": p},
                )
                break

    def predict(
        self, data: Iterable[Any], *, expected: Any | None = None
    ) -> Any:
        """Predict using one of the loaded model versions."""
        if not self.weights:
            raise RuntimeError("No traffic weights configured")
        version = self._choose_version()
        model = self.models.get(version)
        if model is None:
            raise RuntimeError(f"Model version {version} not loaded")
        start = perf_counter()
        result = model.predict(data)
        latency = perf_counter() - start
        success: Optional[bool] = None
        if expected is not None:
            try:
                success = bool(result == expected)
            except Exception:  # pragma: no cover - non-comparable types
                try:
                    success = bool((result == expected).all())
                except Exception:
                    success = None
        self.logger.info(
            "ab_test_prediction",
            extra={"version": version, "success": success, "latency": latency},
        )
        self._record_metrics(version, success, latency)
        self._evaluate_promotion()
        return result


__all__ = ["ModelABTester"]
