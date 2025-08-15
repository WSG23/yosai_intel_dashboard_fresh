"""Lightweight Prometheus metrics used by the circuit breaker tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from prometheus_client import Counter
else:  # pragma: no cover - metrics are optional during tests
    try:
        from prometheus_client import Counter
    except Exception:  # pragma: no cover - fallback when Prometheus unavailable

        class Counter:  # type: ignore[no-redef]
            def __init__(self, *a: object, **k: object) -> None: ...

            def labels(self, *a: object, **k: object) -> "Counter":
                return self

            def inc(self, *a: object, **k: object) -> None:
                return None


circuit_breaker_state = Counter(
    "circuit_breaker_state_transitions_total",
    "Count of circuit breaker state transitions",
    ["name", "state"],
)

__all__ = ["Counter", "circuit_breaker_state"]
