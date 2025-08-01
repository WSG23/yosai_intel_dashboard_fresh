"""Prometheus metrics for API request performance."""

from __future__ import annotations

from prometheus_client import REGISTRY, Histogram
from prometheus_client.core import CollectorRegistry

_DEFAULT_BUCKETS = (
    0.005,
    0.01,
    0.025,
    0.05,
    0.1,
    0.25,
    0.5,
    1.0,
    2.5,
    5.0,
    10.0,
)

if "api_request_duration_seconds" not in REGISTRY._names_to_collectors:
    request_duration = Histogram(
        "api_request_duration_seconds",
        "API request latency in seconds",
        buckets=_DEFAULT_BUCKETS,
    )
else:  # pragma: no cover - defensive in tests
    request_duration = Histogram(
        "api_request_duration_seconds",
        "API request latency in seconds",
        buckets=_DEFAULT_BUCKETS,
        registry=CollectorRegistry(),
    )

if "async_task_duration_seconds" not in REGISTRY._names_to_collectors:
    async_task_duration = Histogram(
        "async_task_duration_seconds",
        "Async task execution time in seconds",
        buckets=_DEFAULT_BUCKETS,
    )
else:  # pragma: no cover - defensive in tests
    async_task_duration = Histogram(
        "async_task_duration_seconds",
        "Async task execution time in seconds",
        buckets=_DEFAULT_BUCKETS,
        registry=CollectorRegistry(),
    )

__all__ = ["request_duration", "async_task_duration"]
