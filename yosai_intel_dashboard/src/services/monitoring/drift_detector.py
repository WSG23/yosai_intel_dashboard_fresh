from __future__ import annotations

"""Simple prediction drift detector with Prometheus and OpenTelemetry hooks."""

from dataclasses import dataclass, field
from typing import Callable, Iterable, List
import logging

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

logger = logging.getLogger(__name__)

if "prediction_drift_ratio" not in REGISTRY._names_to_collectors:
    prediction_drift_ratio = Gauge(
        "prediction_drift_ratio",
        "Mean absolute difference between predictions and thresholds",
    )
else:  # pragma: no cover - defensive
    prediction_drift_ratio = Gauge(
        "prediction_drift_ratio",
        "Mean absolute difference between predictions and thresholds",
        registry=CollectorRegistry(),
    )


@dataclass
class DriftDetector:
    """Detect drift based on deviation between values and thresholds.

    Parameters
    ----------
    tolerance:
        Mean absolute difference required to trigger a drift alert.
    alert_func:
        Callback invoked with the calculated difference when drift is
        detected. Defaults to logging a warning.
    """

    tolerance: float = 0.0
    alert_func: Callable[[float], None] | None = None
    last_values: List[float] = field(default_factory=list, init=False)
    last_thresholds: List[float] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        if self.alert_func is None:
            self.alert_func = lambda diff: logger.warning(
                "Prediction drift detected: %.4f", diff
            )

    def detect(self, values: Iterable[float], thresholds: Iterable[float]) -> bool:
        """Return True when mean absolute diff exceeds ``tolerance``."""
        self.last_values = list(values)
        self.last_thresholds = list(thresholds)
        diffs = [abs(v - t) for v, t in zip(self.last_values, self.last_thresholds)]
        mean_diff = float(sum(diffs) / len(diffs)) if diffs else 0.0
        prediction_drift_ratio.set(mean_diff)
        with tracer.start_as_current_span("drift_detect") as span:
            span.set_attribute("drift.mean_diff", mean_diff)
        if mean_diff > self.tolerance:
            assert self.alert_func is not None
            self.alert_func(mean_diff)
            return True
        return False


__all__ = ["DriftDetector", "prediction_drift_ratio"]
