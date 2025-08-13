"""Lightweight Prometheus metrics used by the circuit breaker tests."""

from __future__ import annotations

from typing import Any

try:  # pragma: no cover - metrics are optional during tests
    from prometheus_client import Counter  # type: ignore[import-not-found]
except Exception:  # pragma: no cover - fallback when Prometheus unavailable

    class Counter:  # type: ignore[misc, no-redef]
        def __init__(self, *a: Any, **k: Any) -> None: ...

        def labels(self, *a: Any, **k: Any) -> "Counter":
            return self

        def inc(self, *a: Any, **k: Any) -> None:
            return None


circuit_breaker_state = Counter(
    "circuit_breaker_state_transitions_total",
    "Count of circuit breaker state transitions",
    ["name", "state"],
)
