from __future__ import annotations

"""Prometheus metrics for ML model performance."""

import asyncio

from prometheus_client import REGISTRY, Gauge, start_http_server
from prometheus_client.core import CollectorRegistry

from yosai_intel_dashboard.src.core.events import EventBus
from yosai_intel_dashboard.src.services.model_monitoring_service import (
    ModelMonitoringService,
)
from yosai_intel_dashboard.src.services.publishing_service import PublishingService

if "model_accuracy" not in REGISTRY._names_to_collectors:
    model_accuracy = Gauge("model_accuracy", "Latest model accuracy")
    model_precision = Gauge("model_precision", "Latest model precision")
    model_recall = Gauge("model_recall", "Latest model recall")
    model_f1 = Gauge("model_f1_score", "Latest model F1 score")
    model_latency = Gauge("model_latency_ms", "Latest prediction latency in ms")
    model_throughput = Gauge(
        "model_throughput", "Latest prediction throughput (events/sec)"
    )
    model_drift = Gauge("model_drift_score", "Latest data drift score")
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
    model_f1 = Gauge(
        "model_f1_score", "Latest model F1 score", registry=CollectorRegistry()
    )
    model_latency = Gauge(
        "model_latency_ms",
        "Latest prediction latency in ms",
        registry=CollectorRegistry(),
    )
    model_throughput = Gauge(
        "model_throughput",
        "Latest prediction throughput (events/sec)",
        registry=CollectorRegistry(),
    )
    model_drift = Gauge(
        "model_drift_score",
        "Latest data drift score",
        registry=CollectorRegistry(),
    )

_metrics_started = False
_monitoring_service = ModelMonitoringService()
_publisher = PublishingService(EventBus())


def start_model_metrics_server(port: int = 8005) -> None:
    """Expose model metrics on ``port`` if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


def update_model_metrics(
    metrics, *, model_name: str = "model", version: str = ""
) -> None:
    """Update Prometheus gauges using ``metrics`` and persist history."""

    model_accuracy.set(metrics.accuracy)
    model_precision.set(metrics.precision)
    model_recall.set(metrics.recall)
    if hasattr(metrics, "f1"):
        model_f1.set(metrics.f1)
    if hasattr(metrics, "latency"):
        model_latency.set(metrics.latency)
    if hasattr(metrics, "throughput"):
        model_throughput.set(metrics.throughput)
    if hasattr(metrics, "drift"):
        model_drift.set(metrics.drift)

    # Record metrics to TimescaleDB
    for name in [
        "accuracy",
        "precision",
        "recall",
        "f1",
        "latency",
        "throughput",
        "drift",
    ]:
        if hasattr(metrics, name):
            value = getattr(metrics, name)
            asyncio.run(
                _monitoring_service.log_evaluation(
                    model_name,
                    version,
                    name,
                    float(value),
                    "performance" if name != "drift" else "drift",
                    "ok",
                )
            )

    # Broadcast update over event bus / websockets
    payload = {name: getattr(metrics, name) for name in metrics.__dict__}
    payload.update({"model_name": model_name, "version": version})
    _publisher.publish(payload)


__all__ = [
    "model_accuracy",
    "model_precision",
    "model_recall",
    "model_f1",
    "model_latency",
    "model_throughput",
    "model_drift",
    "start_model_metrics_server",
    "update_model_metrics",
]
