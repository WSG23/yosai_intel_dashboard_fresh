"""Prometheus metrics for database connection pool health."""

from __future__ import annotations

from prometheus_client import REGISTRY, Gauge, Histogram
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
    10.0,
)

if "db_pool_current_size" not in REGISTRY._names_to_collectors:
    db_pool_current_size = Gauge(
        "db_pool_current_size", "Current maximum size of the connection pool"
    )
    db_pool_active_connections = Gauge(
        "db_pool_active_connections", "Connections currently in use"
    )
    db_pool_wait_seconds = Histogram(
        "db_pool_wait_seconds",
        "Time spent waiting for a database connection",
        buckets=_DEFAULT_BUCKETS,
    )
else:  # pragma: no cover - defensive in tests
    db_pool_current_size = Gauge(
        "db_pool_current_size",
        "Current maximum size of the connection pool",
        registry=CollectorRegistry(),
    )
    db_pool_active_connections = Gauge(
        "db_pool_active_connections",
        "Connections currently in use",
        registry=CollectorRegistry(),
    )
    db_pool_wait_seconds = Histogram(
        "db_pool_wait_seconds",
        "Time spent waiting for a database connection",
        buckets=_DEFAULT_BUCKETS,
        registry=CollectorRegistry(),
    )

__all__ = [
    "db_pool_current_size",
    "db_pool_active_connections",
    "db_pool_wait_seconds",
]
