from __future__ import annotations

"""Scheduled monitoring of active ML models."""

import threading
import warnings
from typing import Optional

from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry
from yosai_intel_dashboard.src.infrastructure.config import get_monitoring_config
from yosai_intel_dashboard.src.utils.scipy_compat import stats

from .model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)
from .prometheus.model_metrics import update_model_metrics


class ModelMonitor:
    """Periodically evaluate active models and check for drift."""

    def __init__(
        self,
        registry: ModelRegistry,
        *,
        interval_minutes: Optional[int] = None,
    ) -> None:
        cfg = get_monitoring_config()
        default_interval = getattr(cfg, "model_check_interval_minutes", 60)
        self.drift_threshold_ks = getattr(cfg, "drift_threshold_ks", 0.1)
        self.drift_threshold_psi = getattr(cfg, "drift_threshold_psi", 0.1)
        self.drift_threshold_wasserstein = getattr(
            cfg, "drift_threshold_wasserstein", 0.1
        )
        self.interval_minutes = interval_minutes or default_interval
        self.registry = registry
        self.monitor = get_model_performance_monitor()
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the background evaluation loop."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the evaluation loop."""
        if self._thread:
            self._stop.set()
            self._thread.join()

    # ------------------------------------------------------------------
    def _run(self) -> None:
        interval = self.interval_minutes * 60
        while not self._stop.is_set():
            self.evaluate_active_models()
            self._stop.wait(interval)

    # ------------------------------------------------------------------
    def evaluate_active_models(self) -> None:
        """Evaluate all active models and record metrics."""
        records = self.registry.list_models()
        for rec in records:
            if not getattr(rec, "is_active", False):
                continue
            metrics_dict = rec.metrics or {}
            metrics = ModelMetrics(
                accuracy=metrics_dict.get("accuracy", 0.0),
                precision=metrics_dict.get("precision", 0.0),
                recall=metrics_dict.get("recall", 0.0),
            )
            update_model_metrics(metrics)
            if self.monitor.detect_drift(metrics):
                warnings.warn(
                    f"Model drift detected for {rec.name} {rec.version}",
                    RuntimeWarning,
                )
                self.monitor.baseline = metrics

            # Feature drift checks using registry metrics
            psi_metrics = self.registry.get_drift_metrics(rec.name)
            for feature, psi in psi_metrics.items():
                if psi > self.drift_threshold_psi:
                    warnings.warn(
                        f"PSI drift detected for {rec.name} {feature}: {psi:.4f}",
                        RuntimeWarning,
                    )

            base_features = getattr(self.registry, "_baseline_features", {}).get(
                rec.name
            )
            curr_features = getattr(self.registry, "_latest_features", {}).get(rec.name)
            if base_features is None or curr_features is None:
                continue
            common = base_features.columns.intersection(curr_features.columns)
            for col in common:
                base_col = base_features[col].dropna()
                curr_col = curr_features[col].dropna()
                if base_col.empty or curr_col.empty:
                    continue
                if hasattr(stats, "ks_2samp"):
                    result = stats.ks_2samp(base_col, curr_col)
                    ks_stat = getattr(result, "statistic", result[0])
                    if ks_stat > self.drift_threshold_ks:
                        warnings.warn(
                            f"KS drift detected for {rec.name} {col}: {ks_stat:.4f}",
                            RuntimeWarning,
                        )
                if hasattr(stats, "wasserstein_distance"):
                    w_dist = stats.wasserstein_distance(base_col, curr_col)
                    if w_dist > self.drift_threshold_wasserstein:
                        warnings.warn(
                            (
                                f"Wasserstein drift detected for {rec.name} {col}: "
                                f"{w_dist:.4f}"
                            ),
                            RuntimeWarning,
                        )


__all__ = ["ModelMonitor"]
