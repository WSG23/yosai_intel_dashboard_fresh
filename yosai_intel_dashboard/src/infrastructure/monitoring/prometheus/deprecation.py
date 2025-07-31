"""Prometheus metrics for deprecated function usage."""

from prometheus_client import REGISTRY, Counter, start_http_server
from prometheus_client.core import CollectorRegistry

if "deprecated_function_calls_total" not in REGISTRY._names_to_collectors:
    deprecated_calls = Counter(
        "deprecated_function_calls_total",
        "Count of deprecated function calls",
        ["function"],
    )
else:  # pragma: no cover - defensive
    deprecated_calls = Counter(
        "deprecated_function_calls_total",
        "Count of deprecated function calls",
        ["function"],
        registry=CollectorRegistry(),
    )

_metrics_started = False


def start_deprecation_metrics_server(port: int = 8006) -> None:
    """Expose deprecation metrics on ``port`` if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


def record_deprecated_call(function: str) -> None:
    """Increment Prometheus counter for ``function``."""
    deprecated_calls.labels(function=function).inc()


__all__ = [
    "deprecated_calls",
    "start_deprecation_metrics_server",
    "record_deprecated_call",
]
