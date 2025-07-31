"""Prometheus metrics for API request performance."""

from prometheus_client import REGISTRY, Histogram
from prometheus_client.core import CollectorRegistry

if "api_request_duration_seconds" not in REGISTRY._names_to_collectors:
    request_duration = Histogram(
        "api_request_duration_seconds", "API request latency in seconds"
    )
else:  # pragma: no cover - defensive in tests
    request_duration = Histogram(
        "api_request_duration_seconds",
        "API request latency in seconds",
        registry=CollectorRegistry(),
    )

__all__ = ["request_duration"]
