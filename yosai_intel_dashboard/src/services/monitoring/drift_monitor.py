from __future__ import annotations

"""Scheduled drift monitoring for live predictions.

This module compares live prediction distributions with a baseline at a fixed
interval. Metrics are persisted via a user provided callback and alerts are
emitted when configured thresholds are exceeded.
"""

import logging
from typing import Callable, Dict, List

import pandas as pd

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover
    BackgroundScheduler = None  # type: ignore

from .drift import detect_drift

logger = logging.getLogger(__name__)


class DriftMonitor:
    """Periodically evaluate prediction drift and emit alerts."""

    def __init__(
        self,
        baseline_supplier: Callable[[], pd.DataFrame],
        live_supplier: Callable[[], pd.DataFrame],
        *,
        thresholds: Dict[str, float] | None = None,
        schedule_interval_minutes: int = 60,
        metric_store: Callable[[Dict[str, Dict[str, float]]], None] | None = None,
        alert_func: Callable[[str, Dict[str, float]], None] | None = None,
    ) -> None:
        """Create a new :class:`DriftMonitor`.

        Parameters
        ----------
        baseline_supplier:
            Callable returning the baseline distribution as a DataFrame.
        live_supplier:
            Callable returning the latest predictions as a DataFrame.
        thresholds:
            Optional mapping of metric name (``psi``, ``ks`` or ``wasserstein``)
            to a float threshold. Metrics beyond the threshold trigger
            ``alert_func``.
        schedule_interval_minutes:
            Interval in minutes between drift evaluations.
        metric_store:
            Callback invoked with each metrics dictionary for persistence.
        alert_func:
            Callback invoked with ``(column_name, metrics)`` when drift is
            detected.
        """

        self.baseline_supplier = baseline_supplier
        self.live_supplier = live_supplier
        self.thresholds = thresholds or {"psi": 0.1, "ks": 0.1, "wasserstein": 0.1}
        self.schedule_interval_minutes = schedule_interval_minutes
        self.metric_store = metric_store or (lambda metrics: None)
        self.alert_func = alert_func or (
            lambda col, metrics: logger.warning(
                "Drift detected for %s: %s", col, metrics
            )
        )
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None
        self.history: List[Dict[str, Dict[str, float]]] = []

    # ------------------------------------------------------------------
    def _check_thresholds(self, metrics: Dict[str, Dict[str, float]]) -> None:
        for col, values in metrics.items():
            for metric_name, value in values.items():
                threshold = self.thresholds.get(metric_name)
                if threshold is not None and value > threshold:
                    self.alert_func(col, values)
                    break

    def _run(self) -> None:
        try:
            base = self.baseline_supplier()
            current = self.live_supplier()
            metrics = detect_drift(base, current)
            logger.info("Drift metrics: %s", metrics)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Drift monitor evaluation failed")
            return

        try:
            self.metric_store(metrics)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Drift monitor metric persistence failed")

        self.history.append(metrics)

        try:
            self._check_thresholds(metrics)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Drift monitor threshold check failed")

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the scheduled drift monitoring job."""
        if not self.scheduler:
            raise RuntimeError("APScheduler is required for DriftMonitor")
        self.scheduler.add_job(
            self._run, "interval", minutes=self.schedule_interval_minutes
        )
        self.scheduler.start()

    def stop(self) -> None:
        """Stop the scheduled drift monitoring job."""
        if self.scheduler:
            self.scheduler.shutdown()


__all__ = ["DriftMonitor"]
