import os

from prometheus_client import generate_latest

os.environ.setdefault("CACHE_TTL", "1")

from yosai_intel_dashboard.src.infrastructure.monitoring.request_metrics import (
    request_duration,
)


def test_request_duration_metric_exposed():
    request_duration.observe(0.2)
    metrics = generate_latest(request_duration)
    assert b"api_request_duration_seconds_count" in metrics
