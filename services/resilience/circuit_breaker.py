from __future__ import annotations

"""Asynchronous circuit breaker utilities.

This module provides a lightweight circuit breaker implementation used
throughout the code base. It intentionally keeps dependencies minimal so it
can be imported in isolation during tests. Repeated failures trip the breaker
into an open state and after a cool down period the breaker will allow a
single trial request (``half-open``) to determine if the underlying dependency
has recovered.
"""

import asyncio
import time
from types import TracebackType
from typing import Awaitable, Callable, ParamSpec, TypeVar

P = ParamSpec("P")
R = TypeVar("R")

try:  # pragma: no cover - optional during tests
    from yosai_intel_dashboard.src.infrastructure.monitoring.error_budget import (
        record_error,
    )
except Exception:  # pragma: no cover - if monitoring deps missing

    def record_error(service: str) -> None:
        """Fallback ``record_error`` when monitoring is optional."""
        return None


from .metrics import Counter

_circuit_breaker_state: Counter | None = None


def _get_circuit_breaker_state() -> Counter:
    """Lazily import the Prometheus metric for circuit breaker state."""
    global _circuit_breaker_state
    if _circuit_breaker_state is None:
        from .metrics import circuit_breaker_state  # local import to avoid heavy deps

        _circuit_breaker_state = circuit_breaker_state
    return _circuit_breaker_state


class CircuitBreakerOpen(Exception):
    """Raised when an operation is attempted while the circuit is open."""


class CircuitBreaker:
    """Asynchronous circuit breaker.

    Parameters
    ----------
    failure_threshold:
        Number of consecutive failures before the circuit opens.
    recovery_timeout:
        Seconds to wait before allowing a trial request after opening.
    name:
        Optional identifier used for metrics and error budget recording.
    """

    def __init__(
        self, failure_threshold: int, recovery_timeout: int, name: str | None = None
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._name = name or "circuit"
        self._failures = 0
        self._opened_at: float | None = None
        self._state = "closed"
        self._lock = asyncio.Lock()

    async def record_success(self) -> None:
        """Reset failure counter and close the circuit."""
        async with self._lock:
            self._failures = 0
            if self._state != "closed":
                _get_circuit_breaker_state().labels(self._name, "closed").inc()
            self._state = "closed"
            self._opened_at = None

    async def record_failure(self) -> None:
        """Record a failed attempt and open the circuit if threshold exceeded."""
        async with self._lock:
            self._failures += 1
            record_error(self._name)
            if self._failures >= self.failure_threshold and self._state != "open":
                _get_circuit_breaker_state().labels(self._name, "open").inc()
                self._state = "open"
                self._opened_at = time.time()

    async def allows_request(self) -> bool:
        """Return ``True`` if a call should be attempted."""
        async with self._lock:
            if self._state == "open":
                if (
                    self._opened_at is not None
                    and time.time() - self._opened_at >= self.recovery_timeout
                ):
                    _get_circuit_breaker_state().labels(self._name, "half_open").inc()
                    self._state = "half_open"
                    return True
                return False
            return True

    async def __aenter__(self) -> "CircuitBreaker":
        if not await self.allows_request():
            raise CircuitBreakerOpen("circuit breaker is open")
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if exc is None:
            await self.record_success()
        else:
            await self.record_failure()

    def __call__(self, func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        cb = self

        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if not await cb.allows_request():
                raise CircuitBreakerOpen("circuit breaker is open")
            try:
                result = await func(*args, **kwargs)
            except Exception:
                await cb.record_failure()
                raise
            else:
                await cb.record_success()
                return result

        return wrapper


def circuit_breaker(
    failure_threshold: int, recovery_timeout: int, name: str | None = None
) -> Callable[[Callable[P, Awaitable[R]]], Callable[P, Awaitable[R]]]:
    """Decorator factory creating a :class:`CircuitBreaker` per function."""
    cb = CircuitBreaker(failure_threshold, recovery_timeout, name)

    def decorator(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[R]]:
        return cb(func)

    return decorator


__all__ = ["CircuitBreaker", "CircuitBreakerOpen", "circuit_breaker"]
