from __future__ import annotations

import asyncio
import time
from typing import Any, Awaitable, Callable


class CircuitBreakerOpen(Exception):
    """Raised when the circuit is open and requests are blocked."""


class CircuitBreaker:
    """Simple asynchronous circuit breaker."""

    def __init__(self, failure_threshold: int, recovery_timeout: int, *, name: str | None = None) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None
        self._state = "closed"
        self._lock = asyncio.Lock()
        self._name = name or "circuit"

    async def record_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._opened_at = None
            self._state = "closed"

    async def record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold and self._state != "open":
                self._state = "open"
                self._opened_at = time.time()

    async def allows_request(self) -> bool:
        async with self._lock:
            if self._state == "open":
                if self._opened_at and time.time() - self._opened_at >= self.recovery_timeout:
                    self._state = "half_open"
                    return True
                return False
            return True

    async def __aenter__(self) -> "CircuitBreaker":
        if not await self.allows_request():
            raise CircuitBreakerOpen(f"{self._name} circuit open")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc is None:
            await self.record_success()
        else:
            await self.record_failure()

    def __call__(self, func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        cb = self

        async def wrapper(*args, **kwargs):
            if not await cb.allows_request():
                raise CircuitBreakerOpen(f"{cb._name} circuit open")
            try:
                result = await func(*args, **kwargs)
            except Exception:
                await cb.record_failure()
                raise
            else:
                await cb.record_success()
                return result

        return wrapper

