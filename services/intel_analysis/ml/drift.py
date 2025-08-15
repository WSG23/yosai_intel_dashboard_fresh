from __future__ import annotations

"""Drift detection utilities for model predictions."""

from dataclasses import dataclass, field
from typing import Callable, Iterable, List

import logging

try:  # optional dependency
    from prometheus_client import REGISTRY, Histogram, Counter
    from prometheus_client.core import CollectorRegistry
except Exception:  # pragma: no cover - dependency optional
    REGISTRY = type("R", (), {"_names_to_collectors": {}})()  # type: ignore
    Histogram = Counter = None  # type: ignore
    CollectorRegistry = None  # type: ignore

from opentelemetry import trace

tracer = trace.get_tracer(__name__)

if Histogram and Counter:
    if "prediction_threshold_ratio" not in REGISTRY._names_to_collectors:
        prediction_ratio = Histogram(
            "prediction_threshold_ratio", "Ratio of prediction to threshold"
        )
        drift_alerts = Counter(
            "prediction_drift_alerts_total", "Number of drift alerts triggered"
        )
    else:  # pragma: no cover - defensive for test stubs
        _reg = CollectorRegistry() if CollectorRegistry else None
        prediction_ratio = Histogram(
            "prediction_threshold_ratio",
            "Ratio of prediction to threshold",
            registry=_reg,
        )
        drift_alerts = Counter(
            "prediction_drift_alerts_total",
            "Number of drift alerts triggered",
            registry=_reg,
        )
else:  # pragma: no cover - metrics unavailable
    prediction_ratio = None
    drift_alerts = None


@dataclass
class ThresholdDriftDetector:
    """Detect drift based on prediction/threshold ratios.

    Values exceeding ``ratio_threshold`` are considered drift. Metrics are
    emitted to Prometheus (when available) and recorded to OpenTelemetry spans.
    An optional ``alert_func`` can be provided to handle drift events.
    """

    ratio_threshold: float = 1.2
    metric: any | None = None
    alert_counter: any | None = None
    alert_func: Callable[[List[float], List[float]], None] | None = None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    # store last seen values for introspection/testing
    values: List[float] | None = None
    thresholds: List[float] | None = None

    def __post_init__(self) -> None:
        if self.metric is None:
            self.metric = prediction_ratio
        if self.alert_counter is None:
            self.alert_counter = drift_alerts
        if self.alert_func is None:
            self.alert_func = lambda v, t: self.logger.warning(
                "Drift detected: values=%s thresholds=%s", v, t
            )

    def detect(self, values: Iterable[float], thresholds: Iterable[float]) -> bool:
        self.values = list(values)
        self.thresholds = list(thresholds)
        ratios = [
            v / t if t else float("inf") for v, t in zip(self.values, self.thresholds)
        ]

        drift = any(r > self.ratio_threshold for r in ratios)

        if self.metric is not None:
            for r in ratios:
                try:
                    self.metric.observe(r)
                except Exception:  # pragma: no cover - metrics stub
                    pass

        with tracer.start_as_current_span("drift_detect") as span:
            span.set_attribute("ratios", ratios)
            span.set_attribute("drift", drift)

        if drift:
            if self.alert_counter is not None:
                try:
                    self.alert_counter.inc()
                except Exception:  # pragma: no cover - metrics stub
                    pass
            try:
                self.alert_func(self.values, self.thresholds)
            except Exception:  # pragma: no cover - defensive
                self.logger.exception("Alert function failed")

        return drift


__all__ = ["ThresholdDriftDetector"]
