"""Prometheus metrics for ML model performance."""

from prometheus_client import REGISTRY, Gauge, start_http_server
from prometheus_client.core import CollectorRegistry

if "model_accuracy" not in REGISTRY._names_to_collectors:
    model_accuracy = Gauge("model_accuracy", "Latest model accuracy")
    model_precision = Gauge("model_precision", "Latest model precision")
    model_recall = Gauge("model_recall", "Latest model recall")
else:  # pragma: no cover - defensive in tests
    model_accuracy = Gauge(
        "model_accuracy", "Latest model accuracy", registry=CollectorRegistry()
    )
    model_precision = Gauge(
        "model_precision", "Latest model precision", registry=CollectorRegistry()
    )
    model_recall = Gauge(
        "model_recall", "Latest model recall", registry=CollectorRegistry()
    )

_metrics_started = False


def start_model_metrics_server(port: int = 8005) -> None:
    """Expose model metrics on ``port`` if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


def update_model_metrics(metrics) -> None:
    """Update Prometheus gauges using ``metrics``."""
    model_accuracy.set(metrics.accuracy)
    model_precision.set(metrics.precision)
    model_recall.set(metrics.recall)


__all__ = [
    "model_accuracy",
    "model_precision",
    "model_recall",
    "start_model_metrics_server",
    "update_model_metrics",
]
