from __future__ import annotations

"""Scheduled monitoring of active ML models."""

import asyncio
import threading
import warnings
from typing import Optional

from yosai_intel_dashboard.src.infrastructure.config import get_monitoring_config
from yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor import (
    ModelMetrics,
    get_model_performance_monitor,
)
from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry
from yosai_intel_dashboard.src.services.timescale.manager import TimescaleDBManager


class ModelMonitor:
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
        self.db = TimescaleDBManager()
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
    def _calculate_metrics(self, model_name: str) -> ModelMetrics:
        """Fetch recent predictions and labels and compute metrics.

        If fetching data fails or no data is available, return zeroed metrics.
        """

        async def _fetch() -> list[tuple[object, object]]:
            query = (
                "SELECT prediction, actual FROM model_predictions "
                "WHERE model_name = $1 ORDER BY timestamp DESC LIMIT 1000"
            )
            rows = await self.db.fetch(query, model_name)
            return [(r["prediction"], r["actual"]) for r in rows]

        try:
            pairs = asyncio.run(_fetch())
        except Exception:
            return ModelMetrics(accuracy=0.0, precision=0.0, recall=0.0)

        if not pairs:
            return ModelMetrics(accuracy=0.0, precision=0.0, recall=0.0)

        preds, labels = zip(*pairs)
        total = len(labels)
        correct = sum(p == t for p, t in zip(preds, labels))
        accuracy = correct / total

        # Binary classification assumption
        pos_label = 1
        tp = sum(1 for p, t in zip(preds, labels) if p == pos_label and t == pos_label)
        fp = sum(1 for p, t in zip(preds, labels) if p == pos_label and t != pos_label)
        fn = sum(1 for p, t in zip(preds, labels) if p != pos_label and t == pos_label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0

        return ModelMetrics(accuracy=accuracy, precision=precision, recall=recall)

    # ------------------------------------------------------------------
    def evaluate_active_models(self) -> None:
        """Evaluate all active models and record metrics."""
        records = self.registry.list_models()
        for rec in records:
            if not getattr(rec, "is_active", False):
                continue
            metrics = self._calculate_metrics(rec.name)
            self.monitor.log_metrics(metrics)
            if self.monitor.detect_drift(metrics):
                warnings.warn(
                    f"Model drift detected for {rec.name} {rec.version}",
                    RuntimeWarning,
                )
                self.monitor.baseline = metrics


__all__ = ["ModelMonitor"]
