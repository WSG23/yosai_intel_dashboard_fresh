"""Prometheus metrics tracking service decisions and their latency."""

from __future__ import annotations

import time
from contextlib import contextmanager

from prometheus_client import REGISTRY, Counter, Histogram
from prometheus_client.core import CollectorRegistry

_DEFAULT_BUCKETS = (
    0.001,
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
)

if "service_decisions_total" not in REGISTRY._names_to_collectors:
    decision_count = Counter(
        "service_decisions_total",
        "Total number of key decisions made",
        ["service", "decision"],
    )
else:  # pragma: no cover - defensive in tests
    decision_count = Counter(
        "service_decisions_total",
        "Total number of key decisions made",
        ["service", "decision"],
        registry=CollectorRegistry(),
    )

if "service_decision_latency_seconds" not in REGISTRY._names_to_collectors:
    decision_latency = Histogram(
        "service_decision_latency_seconds",
        "Latency of key decisions in seconds",
        ["service", "decision"],
        buckets=_DEFAULT_BUCKETS,
    )
else:  # pragma: no cover - defensive in tests
    decision_latency = Histogram(
        "service_decision_latency_seconds",
        "Latency of key decisions in seconds",
        ["service", "decision"],
        buckets=_DEFAULT_BUCKETS,
        registry=CollectorRegistry(),
    )


def record_decision(service: str, decision: str, elapsed: float) -> None:
    """Record a decision taken by *service* and observe its latency."""
    decision_count.labels(service=service, decision=decision).inc()
    decision_latency.labels(service=service, decision=decision).observe(elapsed)


@contextmanager
def track_decision_latency(service: str, decision: str):
    """Context manager that measures and records decision latency."""
    start = time.perf_counter()
    try:
        yield
    finally:
        record_decision(service, decision, time.perf_counter() - start)


__all__ = [
    "decision_count",
    "decision_latency",
    "record_decision",
    "track_decision_latency",
]
