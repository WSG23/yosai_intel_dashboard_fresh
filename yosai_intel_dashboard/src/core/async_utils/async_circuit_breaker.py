from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable, Optional


def _get_circuit_breaker_state():
    """Return Prometheus metric for circuit breaker state lazily."""
    from yosai_intel_dashboard.src.services.resilience.metrics import (
        circuit_breaker_state,
    )

    return circuit_breaker_state


class CircuitBreakerOpen(Exception):
    """Raised when an operation is attempted while the circuit is open."""


class CircuitBreaker:
    """Asynchronous circuit breaker.

    Parameters
    ----------
    failure_threshold: int
        Number of consecutive failures before the circuit opens.
    recovery_timeout: int
        Seconds to wait before allowing a trial request after opening.
    name: str | None
        Optional identifier used for Prometheus metrics.
    """

    def __init__(
        self, failure_threshold: int, recovery_timeout: int, name: str | None = None
    ) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._name = name or "circuit"
        self._failures = 0
        self._opened_at: Optional[float] = None
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
            if self._failures >= self.failure_threshold and self._state != "open":
                _get_circuit_breaker_state().labels(self._name, "open").inc()
                self._state = "open"
                self._opened_at = time.time()

    async def allows_request(self) -> bool:
        """Return ``True`` if a call should be attempted."""
        async with self._lock:
            if self._state == "open":
                if (
                    self._opened_at
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

    async def __aexit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if exc is None:
            await self.record_success()
        else:
            await self.record_failure()

    def __call__(
        self, func: Callable[..., Awaitable[Any]]
    ) -> Callable[..., Awaitable[Any]]:
        cb = self

        async def wrapper(*args: Any, **kwargs: Any) -> Any:
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
):
    """Decorator factory creating a :class:`CircuitBreaker` per function."""
    cb = CircuitBreaker(failure_threshold, recovery_timeout, name)

    def decorator(func: Callable[..., Awaitable[Any]]):
        return cb(func)

    return decorator


__all__ = ["CircuitBreaker", "CircuitBreakerOpen", "circuit_breaker"]
