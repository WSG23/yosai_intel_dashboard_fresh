"""Prometheus counters for database query metrics.

Import ``queries_total`` and ``query_errors_total`` to track how many
database queries were executed and how many failed.
"""

from prometheus_client import Counter, Gauge

queries_total = Counter("database_queries_total", "Total database queries executed")
query_errors_total = Counter(
    "database_query_errors_total", "Total database query errors"
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
    "queries_total",
    "query_errors_total",
    "pool_utilization",
    "health_check_failures_total",
    "health_check_retries_total",
]
