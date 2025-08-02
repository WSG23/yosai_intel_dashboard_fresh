"""Prometheus metrics for clean architecture migration."""

from prometheus_client import (
    REGISTRY,
    Counter,
    Gauge,
    Histogram,
    start_http_server,
)
from prometheus_client.core import CollectorRegistry

if "import_resolution_seconds" not in REGISTRY._names_to_collectors:
    import_resolution_histogram = Histogram(
        "import_resolution_seconds",
        "Time spent resolving imports",
        buckets=[0.01, 0.1, 0.5, 1, 2, 5],
    )
    legacy_import_counter = Counter(
        "legacy_import_usage_total",
        "Count of legacy import usages",
    )
    structure_validation_gauge = Gauge(
        "structure_validation_status",
        "Status of clean architecture validation",
    )
else:  # pragma: no cover - defensive
    import_resolution_histogram = Histogram(
        "import_resolution_seconds",
        "Time spent resolving imports",
        buckets=[0.01, 0.1, 0.5, 1, 2, 5],
        registry=CollectorRegistry(),
    )
    legacy_import_counter = Counter(
        "legacy_import_usage_total",
        "Count of legacy import usages",
        registry=CollectorRegistry(),
    )
    structure_validation_gauge = Gauge(
        "structure_validation_status",
        "Status of clean architecture validation",
        registry=CollectorRegistry(),
    )

_metrics_started = False


def start_clean_architecture_metrics_server(port: int = 8007) -> None:
    """Expose clean architecture metrics on ``port`` if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


def record_import_resolution(duration: float) -> None:
    """Observe import resolution ``duration`` in seconds."""
    import_resolution_histogram.observe(duration)


def increment_legacy_import() -> None:
    """Increment legacy import counter."""
    legacy_import_counter.inc()


def set_structure_validation(status: int) -> None:
    """Set structure validation gauge to ``status``."""
    structure_validation_gauge.set(status)


__all__ = [
    "import_resolution_histogram",
    "legacy_import_counter",
    "structure_validation_gauge",
    "start_clean_architecture_metrics_server",
    "record_import_resolution",
    "increment_legacy_import",
    "set_structure_validation",
]
