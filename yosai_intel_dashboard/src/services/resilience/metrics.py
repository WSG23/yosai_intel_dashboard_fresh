from __future__ import annotations

from prometheus_client import REGISTRY, Counter, start_http_server
from prometheus_client.core import CollectorRegistry

# Counter tracking circuit breaker state transitions. Avoid duplicate
# registration when the module is imported multiple times in tests.
# Counter tracking circuit breaker state transitions. Avoid duplicate
# registration when the module is imported multiple times in tests.
if "circuit_breaker_state_transitions_total" not in REGISTRY._names_to_collectors:
    circuit_breaker_state = Counter(
        "circuit_breaker_state_transitions_total",
        "Count of circuit breaker state transitions",
        ["name", "state"],
    )
else:
    circuit_breaker_state = Counter(
        "circuit_breaker_state_transitions_total",
        "Count of circuit breaker state transitions",
        ["name", "state"],
        registry=CollectorRegistry(),
    )


def _counter(name: str, documentation: str) -> Counter:
    if name not in REGISTRY._names_to_collectors:
        return Counter(name, documentation, ["name"])
    return Counter(name, documentation, ["name"], registry=CollectorRegistry())


dependency_recovery_attempts = _counter(
    "dependency_recovery_attempts_total",
    "Number of recovery attempts for an external dependency",
)
dependency_recovery_successes = _counter(
    "dependency_recovery_successes_total",
    "Number of successful recovery attempts for an external dependency",
)

_metrics_started = False


def start_metrics_server(port: int = 8003) -> None:
    """Expose metrics on the given port if not already started."""
    global _metrics_started
    if not _metrics_started:
        start_http_server(port)
        _metrics_started = True


__all__ = [
    "circuit_breaker_state",
    "dependency_recovery_attempts",
    "dependency_recovery_successes",
    "start_metrics_server",
]
