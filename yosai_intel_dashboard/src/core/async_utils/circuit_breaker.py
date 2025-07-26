from __future__ import annotations

"""Circuit breaker implementation for async operations."""

import asyncio
import time
from typing import Awaitable, Callable, TypeVar

T = TypeVar("T")


class AsyncCircuitOpen(Exception):
    """Raised when the circuit is open and calls are blocked."""


class AsyncCircuitBreaker:
    """Simple asynchronous circuit breaker."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60) -> None:
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self._failures = 0
        self._opened_at: float | None = None
        self._lock = asyncio.Lock()

    async def allows(self) -> bool:
        async with self._lock:
            if self._opened_at is None:
                return True
            if time.time() - self._opened_at >= self.recovery_timeout:
                self._failures = 0
                self._opened_at = None
                return True
            return False

    async def record_success(self) -> None:
        async with self._lock:
            self._failures = 0
            self._opened_at = None

    async def record_failure(self) -> None:
        async with self._lock:
            self._failures += 1
            if self._failures >= self.failure_threshold and self._opened_at is None:
                self._opened_at = time.time()

    async def __aenter__(self) -> "AsyncCircuitBreaker":
        if not await self.allows():
            raise AsyncCircuitOpen("circuit breaker open")
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        if exc is None:
            await self.record_success()
        else:
            await self.record_failure()

    def __call__(
        self, func: Callable[..., Awaitable[T]]
    ) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs):
            if not await self.allows():
                raise AsyncCircuitOpen("circuit breaker open")
            try:
                result = await func(*args, **kwargs)
            except Exception:
                await self.record_failure()
                raise
            await self.record_success()
            return result

        return wrapper


__all__ = ["AsyncCircuitBreaker", "AsyncCircuitOpen"]
