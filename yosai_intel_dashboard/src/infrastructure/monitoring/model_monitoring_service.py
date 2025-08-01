from __future__ import annotations

"""Scheduled monitoring of active ML models with robust error handling."""

import logging
import threading
import time
import warnings
from typing import Optional

from yosai_intel_dashboard.src.infrastructure.config import get_monitoring_config

from yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.model_metrics import (
    update_model_metrics,
)
from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry

LOGGER = logging.getLogger(__name__)


class ModelMonitoringService:
    """Periodically evaluate active models and check for drift."""

    def __init__(
        self,
        registry: ModelRegistry,
        *,
        interval_minutes: Optional[int] = None,
    ) -> None:
        cfg = get_monitoring_config()
        mm_cfg = getattr(cfg, "model_monitor", {})
        if isinstance(mm_cfg, dict):
            default_interval = mm_cfg.get("evaluation_interval_minutes", 60)
        else:
            default_interval = getattr(mm_cfg, "evaluation_interval_minutes", 60)
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
        """Evaluate all active models and record metrics with resiliency."""

        records = self.registry.list_models()
        for rec in records:
            if not getattr(rec, "is_active", False):
                continue
            try:
                metrics_dict = rec.metrics or {}
                metrics = ModelMetrics(
                    accuracy=metrics_dict.get("accuracy", 0.0),
                    precision=metrics_dict.get("precision", 0.0),
                    recall=metrics_dict.get("recall", 0.0),
                )

                # Timescale/metric dispatch with exponential backoff
                backoff = 1.0
                while True:
                    try:
                        update_model_metrics(metrics)
                        break
                    except Exception:
                        LOGGER.exception(
                            "Failed to dispatch metrics for %s %s; retrying in %.1fs",
                            getattr(rec, "name", "unknown"),
                            getattr(rec, "version", "unknown"),
                            backoff,
                        )
                        if backoff > 60:
                            LOGGER.error(
                                "Giving up on metrics dispatch for %s %s",
                                getattr(rec, "name", "unknown"),
                                getattr(rec, "version", "unknown"),
                            )
                            break
                        time.sleep(backoff)
                        backoff *= 2

                # Drift detection and alert dispatch
                try:
                    if self.monitor.detect_drift(metrics):
                        try:
                            warnings.warn(
                                f"Model drift detected for {rec.name} {rec.version}",
                                RuntimeWarning,
                            )
                            self.monitor.baseline = metrics
                        except Exception:
                            LOGGER.exception(
                                "Alert dispatch failed for %s %s",
                                getattr(rec, "name", "unknown"),
                                getattr(rec, "version", "unknown"),
                            )
                except Exception:
                    LOGGER.exception(
                        "Drift detection failed for %s %s",
                        getattr(rec, "name", "unknown"),
                        getattr(rec, "version", "unknown"),
                    )

            except Exception:
                LOGGER.exception(
                    "Error evaluating model %s %s",
                    getattr(rec, "name", "unknown"),
                    getattr(rec, "version", "unknown"),
                )



__all__ = ["ModelMonitoringService"]
