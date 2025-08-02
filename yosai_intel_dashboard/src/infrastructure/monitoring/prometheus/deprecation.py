"""Prometheus metrics for deprecated component usage."""

from prometheus_client import REGISTRY, Counter, start_http_server
from prometheus_client.core import CollectorRegistry

if "deprecation_usage_total" not in REGISTRY._names_to_collectors:
    deprecation_usage = Counter(
        "deprecation_usage_total",
        "Count of deprecated component usage",
        ["component"],
    )
else:  # pragma: no cover - defensive
    deprecation_usage = Counter(
        "deprecation_usage_total",
        "Count of deprecated component usage",
        ["component"],
        registry=CollectorRegistry(),
    )

_metrics_started = False


def start_deprecation_metrics_server(port: int = 8006) -> None:
    """Expose deprecation metrics on ``port`` if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


def record_deprecated_call(component: str) -> None:
    """Increment Prometheus counter for ``component``."""
    deprecation_usage.labels(component=component).inc()


__all__ = [
    "deprecation_usage",
    "start_deprecation_metrics_server",
    "record_deprecated_call",
]
