from __future__ import annotations

"""Periodic drift detection for live inference metrics."""

import threading
from statistics import mean
from typing import Optional

from yosai_intel_dashboard.src.infrastructure.config import get_monitoring_config
from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import AlertConfig, AlertDispatcher
from yosai_intel_dashboard.src.core.performance import get_performance_monitor
from yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor import ModelMetrics
from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry


class InferenceDriftJob:
    """Compare live metrics against training metrics at a fixed interval."""

    def __init__(
        self,
        registry: ModelRegistry,
        *,
        interval_minutes: int = 10,
        drift_threshold: float = 0.05,
        dispatcher: Optional[AlertDispatcher] = None,
    ) -> None:
        cfg = get_monitoring_config()
        alert_cfg = getattr(cfg, "alerting", {})
        if dispatcher is None:
            if isinstance(alert_cfg, dict):
                dispatcher = AlertDispatcher(
                    AlertConfig(
                        slack_webhook=alert_cfg.get("slack_webhook"),
                        email=alert_cfg.get("email"),
                        webhook_url=alert_cfg.get("webhook_url"),
                    )
                )
            else:  # pragma: no cover - defensive
                dispatcher = AlertDispatcher(
                    AlertConfig(
                        slack_webhook=getattr(alert_cfg, "slack_webhook", None),
                        email=getattr(alert_cfg, "email", None),
                        webhook_url=getattr(alert_cfg, "webhook_url", None),
                    )
                )
        self.registry = registry
        self.interval_minutes = interval_minutes
        self.drift_threshold = drift_threshold
        self.dispatcher = dispatcher
        self.training_metrics: Optional[ModelMetrics] = None
        self._thread: Optional[threading.Thread] = None
        self._stop = threading.Event()

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the periodic drift evaluation."""
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the background job."""
        if self._thread:
            self._stop.set()
            self._thread.join()

    # ------------------------------------------------------------------
    def _run(self) -> None:
        interval = self.interval_minutes * 60
        while not self._stop.is_set():
            self.evaluate_drift()
            self._stop.wait(interval)

    # ------------------------------------------------------------------
    def _load_training_metrics(self) -> None:
        for rec in self.registry.list_models():
            if getattr(rec, "is_active", False):
                metrics = rec.metrics or {}
                self.training_metrics = ModelMetrics(
                    accuracy=float(metrics.get("accuracy", 0.0)),
                    precision=float(metrics.get("precision", 0.0)),
                    recall=float(metrics.get("recall", 0.0)),
                )
                break

    # ------------------------------------------------------------------
    def evaluate_drift(self) -> None:
        """Compare live metrics with training metrics and send alerts."""
        if self.training_metrics is None:
            self._load_training_metrics()
            if self.training_metrics is None:
                return

        monitor = get_performance_monitor()
        acc = monitor.aggregated_metrics.get("model.accuracy", [])
        prec = monitor.aggregated_metrics.get("model.precision", [])
        rec = monitor.aggregated_metrics.get("model.recall", [])
        if not (acc and prec and rec):
            return
        live = ModelMetrics(
            accuracy=mean(acc),
            precision=mean(prec),
            recall=mean(rec),
        )
        if self._drift_detected(live):
            msg = (
                "Inference drift detected: "
                f"accuracy {live.accuracy:.3f} vs "
                f"{self.training_metrics.accuracy:.3f}, "
                f"precision {live.precision:.3f} vs "
                f"{self.training_metrics.precision:.3f}, "
                f"recall {live.recall:.3f} vs "
                f"{self.training_metrics.recall:.3f}"
            )
            self.dispatcher.send_alert(msg)

    # ------------------------------------------------------------------
    def _drift_detected(self, live: ModelMetrics) -> bool:
        base = self.training_metrics
        if base is None:
            return False
        return any(
            abs(getattr(live, field) - getattr(base, field)) > self.drift_threshold
            for field in ("accuracy", "precision", "recall")
        )


__all__ = ["InferenceDriftJob"]
