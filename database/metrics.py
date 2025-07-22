from prometheus_client import Counter

queries_total = Counter(
    "database_queries_total", "Total database queries executed"
)
query_errors_total = Counter(
    "database_query_errors_total", "Total database query errors"
)

__all__ = ["queries_total", "query_errors_total"]
