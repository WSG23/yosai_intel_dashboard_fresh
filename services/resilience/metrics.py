from prometheus_client import Counter, start_http_server

# Counter tracking circuit breaker state transitions
circuit_breaker_state = Counter(
    "circuit_breaker_state_transitions_total",
    "Count of circuit breaker state transitions",
    ["name", "state"],
)

_metrics_started = False


def start_metrics_server(port: int = 8003) -> None:
    """Expose metrics on the given port if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


__all__ = ["circuit_breaker_state", "start_metrics_server"]
