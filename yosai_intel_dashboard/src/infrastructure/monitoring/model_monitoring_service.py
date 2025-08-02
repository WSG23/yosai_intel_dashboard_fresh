from __future__ import annotations

"""Background service for periodic ML model monitoring."""

from typing import Optional
import threading

from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry
from yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)


class ModelMonitoringService:
    """Periodically evaluate active models and record their metrics."""

    def __init__(self, registry: ModelRegistry, *, interval_seconds: float = 60) -> None:
        self.registry = registry
        self.interval_seconds = interval_seconds
        self.monitor = get_model_performance_monitor()
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the background monitoring thread."""
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the background monitoring thread."""
        if not self._thread:
            return
        self._stop_event.set()
        self._thread.join()
        self._thread = None

    # ------------------------------------------------------------------
    def _run(self) -> None:
        while not self._stop_event.is_set():
            self.run_checks()
            self._stop_event.wait(self.interval_seconds)

    # ------------------------------------------------------------------
    def run_checks(self) -> None:
        """Evaluate all active models and record their metrics."""
        records = self.registry.list_models()
        for rec in records:
            if not getattr(rec, "is_active", False):
                continue
            self._evaluate_model(rec)

    # ------------------------------------------------------------------
    def _evaluate_model(self, record) -> None:
        metrics_dict = getattr(record, "metrics", {}) or {}
        metrics = ModelMetrics(
            accuracy=metrics_dict.get("accuracy", 0.0),
            precision=metrics_dict.get("precision", 0.0),
            recall=metrics_dict.get("recall", 0.0),
        )
        self.monitor.log_metrics(metrics)
        if self.monitor.detect_drift(metrics):
            # Reset baseline if drift detected to avoid repeated warnings
            self.monitor.baseline = metrics


__all__ = ["ModelMonitoringService"]
