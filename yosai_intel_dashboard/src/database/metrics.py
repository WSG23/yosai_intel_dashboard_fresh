"""Prometheus counters for database query metrics.

Import ``queries_total`` and ``query_errors_total`` to track how many
database queries were executed and how many failed.
"""

try:  # pragma: no cover - exercised in tests
    from prometheus_client import Counter, Gauge, Histogram
except ImportError:  # pragma: no cover - exercised in tests
    class _MetricStub:
        """Fallback metric that ignores all operations."""

        def __init__(self, *args, **kwargs) -> None:  # noqa: D401 - trivial
            pass

        # "labels" returns ``self`` so chained calls still succeed.
        def labels(self, *args, **kwargs):
            return self

        # The following methods intentionally perform no action.
        def inc(self, *args, **kwargs) -> None:  # pragma: no cover - no logic
            pass

        def dec(self, *args, **kwargs) -> None:  # pragma: no cover - no logic
            pass

        def set(self, *args, **kwargs) -> None:  # pragma: no cover - no logic
            pass

        def observe(self, *args, **kwargs) -> None:  # pragma: no cover - no logic
            pass

    class Counter(_MetricStub):
        pass

    class Gauge(_MetricStub):
        pass

    class Histogram(_MetricStub):
        pass

queries_total = Counter("database_queries_total", "Total database queries executed")
query_errors_total = Counter(
    "database_query_errors_total", "Total database query errors"
)

query_execution_seconds = Histogram(
    "database_query_execution_seconds",
    "Time spent executing database queries",
)

# Connection pool metrics
pool_utilization = Gauge(
    "database_pool_utilization",
    "Fraction of database connections in use",
)
health_check_failures_total = Counter(
    "database_health_check_failures_total",
    "Total failed database health checks",
)
health_check_retries_total = Counter(
    "database_health_check_retries_total",
    "Total database health check retries",
)

__all__ = [
    "Counter",
    "Gauge",
    "Histogram",
    "queries_total",
    "query_errors_total",
    "query_execution_seconds",
    "pool_utilization",
    "health_check_failures_total",
    "health_check_retries_total",
]
