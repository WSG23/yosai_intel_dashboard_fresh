"""Prometheus metrics for API request performance."""

from __future__ import annotations

from prometheus_client import REGISTRY, Counter, Histogram
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

if "api_request_retry_total" not in REGISTRY._names_to_collectors:
    request_retry_count = Counter(
        "api_request_retry_total",
        "Total number of HTTP request retries",
    )
else:  # pragma: no cover - defensive in tests
    request_retry_count = Counter(
        "api_request_retry_total",
        "Total number of HTTP request retries",
        registry=CollectorRegistry(),
    )

if "api_request_retry_delay_seconds" not in REGISTRY._names_to_collectors:
    request_retry_delay = Histogram(
        "api_request_retry_delay_seconds",
        "Delay before HTTP request retries in seconds",
        buckets=_DEFAULT_BUCKETS,
    )
else:  # pragma: no cover - defensive in tests
    request_retry_delay = Histogram(
        "api_request_retry_delay_seconds",
        "Delay before HTTP request retries in seconds",
        buckets=_DEFAULT_BUCKETS,
        registry=CollectorRegistry(),
    )

# Additional custom API metrics
if "api_upload_files_total" not in REGISTRY._names_to_collectors:
    upload_files_total = Counter(
        "api_upload_files_total",
        "Total number of files uploaded via the API",
    )
else:  # pragma: no cover - defensive in tests
    upload_files_total = Counter(
        "api_upload_files_total",
        "Total number of files uploaded via the API",
        registry=CollectorRegistry(),
    )

if "api_upload_file_bytes" not in REGISTRY._names_to_collectors:
    upload_file_bytes = Histogram(
        "api_upload_file_bytes",
        "Size of uploaded files in bytes",
        buckets=(
            1024,
            10 * 1024,
            100 * 1024,
            1024 * 1024,
            10 * 1024 * 1024,
        ),
    )
else:  # pragma: no cover - defensive in tests
    upload_file_bytes = Histogram(
        "api_upload_file_bytes",
        "Size of uploaded files in bytes",
        buckets=(
            1024,
            10 * 1024,
            100 * 1024,
            1024 * 1024,
            10 * 1024 * 1024,
        ),
        registry=CollectorRegistry(),
    )

if "api_model_monitoring_requests_total" not in REGISTRY._names_to_collectors:
    model_monitoring_requests_total = Counter(
        "api_model_monitoring_requests_total",
        "Total model monitoring retrieval requests",
    )
else:  # pragma: no cover - defensive in tests
    model_monitoring_requests_total = Counter(
        "api_model_monitoring_requests_total",
        "Total model monitoring retrieval requests",
        registry=CollectorRegistry(),
    )

__all__ = [
    "request_duration",
    "async_task_duration",
    "request_retry_count",
    "request_retry_delay",
    "upload_files_total",
    "upload_file_bytes",
    "model_monitoring_requests_total",
]
