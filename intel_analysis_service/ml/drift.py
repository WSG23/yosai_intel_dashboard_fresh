from __future__ import annotations

"""Drift detection utilities for model predictions."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence, Literal

import logging

try:  # optional dependency
    from prometheus_client import REGISTRY, Histogram, Counter
    from prometheus_client.core import CollectorRegistry
except Exception:  # pragma: no cover - dependency optional
    REGISTRY = type("R", (), {"_names_to_collectors": {}})()
    Histogram = Counter = None
    CollectorRegistry = None

try:  # pragma: no cover - optional dependency
    from opentelemetry import trace

    tracer = trace.get_tracer(__name__)
except Exception:  # pragma: no cover - fallback when OpenTelemetry missing

    class _DummySpan:
        def __enter__(self) -> "_DummySpan":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> Literal[False]:
            return False

        def set_attribute(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
            return None

    class _Tracer:
        def start_as_current_span(self, *_a: Any, **_k: Any) -> _DummySpan:
            return _DummySpan()

    tracer = _Tracer()

if Histogram and Counter:
    if "prediction_threshold_ratio" not in REGISTRY._names_to_collectors:
        prediction_ratio = Histogram(
            "prediction_threshold_ratio", "Ratio of prediction to threshold"
        )
        drift_alerts = Counter(
            "prediction_drift_alerts_total", "Number of drift alerts triggered"
        )
        feature_zscores = Histogram(
            "feature_drift_zscore", "Z-score of feature mean drift", ["feature"]
        )
        feature_alerts = Counter(
            "feature_drift_alerts_total", "Number of feature drift alerts", ["feature"]
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
        feature_zscores = Histogram(
            "feature_drift_zscore",
            "Z-score of feature mean drift",
            ["feature"],
            registry=_reg,
        )
        feature_alerts = Counter(
            "feature_drift_alerts_total",
            "Number of feature drift alerts",
            ["feature"],
            registry=_reg,
        )
else:  # pragma: no cover - metrics unavailable
    prediction_ratio = None
    drift_alerts = None
    feature_zscores = None
    feature_alerts = None


@dataclass
class ThresholdDriftDetector:
    """Detect drift based on prediction/threshold ratios.

    Values exceeding ``ratio_threshold`` are considered drift. Metrics are
    emitted to Prometheus (when available) and recorded to OpenTelemetry spans.
    An optional ``alert_func`` can be provided to handle drift events.
    """

    ratio_threshold: float = 1.2
    metric: Any | None = None
    alert_counter: Any | None = None
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
            if self.alert_func is not None:
                try:
                    self.alert_func(self.values, self.thresholds)
                except Exception:  # pragma: no cover - defensive
                    self.logger.exception("Alert function failed")

        return drift


@dataclass
class FeatureStats:
    """Simple container for feature statistics from training."""

    mean: float
    std: float


@dataclass
class FeatureDriftDetector:
    """Detect feature drift using mean and standard deviation."""

    z_threshold: float = 3.0
    metric: Any | None = None
    alert_counter: Any | None = None
    alert_func: Callable[[Dict[str, float]], None] | None = None
    logger: logging.Logger = field(default_factory=lambda: logging.getLogger(__name__))

    last_zscores: Dict[str, float] = field(default_factory=dict, init=False)

    def __post_init__(self) -> None:
        if self.metric is None:
            self.metric = feature_zscores
        if self.alert_counter is None:
            self.alert_counter = feature_alerts
        if self.alert_func is None:
            self.alert_func = lambda d: self.logger.warning(
                "Feature drift detected: %s", d
            )

    def detect(
        self,
        features: Mapping[str, Sequence[float]],
        stats: Mapping[str, FeatureStats],
    ) -> bool:
        """Compare ``features`` to ``stats`` and return True on drift."""

        self.last_zscores = {}
        for name, values in features.items():
            stat = stats.get(name)
            if not stat or not values:
                continue
            mean = float(sum(values) / len(values))
            if stat.std == 0:
                z = float("inf") if mean != stat.mean else 0.0
            else:
                z = abs(mean - stat.mean) / stat.std
            self.last_zscores[name] = z
            if self.metric is not None:
                try:
                    self.metric.labels(name).observe(z)
                except Exception:  # pragma: no cover - metrics stub
                    pass

        drifted = {n: z for n, z in self.last_zscores.items() if z > self.z_threshold}

        if drifted:
            if self.alert_counter is not None:
                for name in drifted:
                    try:
                        self.alert_counter.labels(name).inc()
                    except Exception:  # pragma: no cover - metrics stub
                        pass
            if self.alert_func is not None:
                try:
                    self.alert_func(drifted)
                except Exception:  # pragma: no cover - defensive
                    self.logger.exception("Alert function failed")
            return True
        return False


__all__ = [
    "ThresholdDriftDetector",
    "FeatureStats",
    "FeatureDriftDetector",
]
