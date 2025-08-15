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
    import opentelemetry.trace as trace
    tracer = trace.get_tracer(__name__)
except Exception:  # pragma: no cover - fallback when OpenTelemetry missing
    class _DummySpan:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def set_attribute(self, *args, **kwargs):
            return None

    class _Tracer:
        def start_as_current_span(self, *_a, **_k):
            return _DummySpan()

    tracer = _Tracer()

from prometheus_client import REGISTRY, Gauge
from prometheus_client.core import CollectorRegistry

try:  # pragma: no cover - optional dependency
    from apscheduler.schedulers.background import BackgroundScheduler
except Exception:  # pragma: no cover
    BackgroundScheduler = None  # type: ignore

from .drift import detect_drift

logger = logging.getLogger(__name__)

if "drift_monitor_metric" not in REGISTRY._names_to_collectors:
    drift_monitor_metric = Gauge(
        "drift_monitor_metric", "Latest drift metric", ["column", "metric"]
    )
else:  # pragma: no cover - defensive
    drift_monitor_metric = Gauge(
        "drift_monitor_metric",
        "Latest drift metric",
        ["column", "metric"],
        registry=CollectorRegistry(),
    )


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
        monitoring_hook: Callable[[str], None] | None = None,
        log_path: str | None = None,
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
        self.monitoring_hook = monitoring_hook
        self.log_path = log_path
        self.scheduler = BackgroundScheduler() if BackgroundScheduler else None
        self.history: List[Dict[str, Dict[str, float]]] = []

    # ------------------------------------------------------------------
    def _log(self, message: str) -> None:
        if self.monitoring_hook:
            try:
                self.monitoring_hook(message)
                return
            except Exception:  # pragma: no cover - defensive
                logger.exception("Drift monitor hook failed")
        if self.log_path:
            try:
                with open(self.log_path, "a", encoding="utf-8") as fh:
                    fh.write(message + "\n")
            except Exception:  # pragma: no cover - defensive
                logger.exception("Drift monitor file log failed")

    def _check_thresholds(self, metrics: Dict[str, Dict[str, float]]) -> None:
        for col, values in metrics.items():
            for metric_name, value in values.items():
                threshold = self.thresholds.get(metric_name)
                if threshold is not None and value > threshold:
                    self._log(f"breach:{col}:{metric_name}={value}")
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

        with tracer.start_as_current_span("drift_monitor_run") as span:
            for col, values in metrics.items():
                for metric_name, value in values.items():
                    drift_monitor_metric.labels(col, metric_name).set(value)
                    span.set_attribute(f"drift.{col}.{metric_name}", value)

        try:
            self.metric_store(metrics)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Drift monitor metric persistence failed")

        self.history.append(metrics)
        self._log(f"comparison:{metrics}")

        try:
            self._check_thresholds(metrics)
        except Exception:  # pragma: no cover - defensive
            logger.exception("Drift monitor threshold check failed")

    def get_recent_history(self, limit: int | None = None) -> List[Dict[str, Dict[str, float]]]:
        """Return the most recent drift metrics."""
        if limit is None:
            return list(self.history)
        return self.history[-limit:]

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


__all__ = ["DriftMonitor", "drift_monitor_metric"]
