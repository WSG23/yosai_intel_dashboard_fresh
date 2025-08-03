"""Lightweight Prometheus metrics used by the circuit breaker tests."""

try:  # pragma: no cover - metrics are optional during tests
    from prometheus_client import Counter
except Exception:  # pragma: no cover - fallback when Prometheus unavailable

    class Counter:  # type: ignore
        def __init__(self, *a, **k) -> None: ...
        def labels(self, *a, **k):
            return self

        def inc(self, *a, **k) -> None:
            return None


circuit_breaker_state = Counter(
    "circuit_breaker_state_transitions_total",
    "Count of circuit breaker state transitions",
    ["name", "state"],
)
