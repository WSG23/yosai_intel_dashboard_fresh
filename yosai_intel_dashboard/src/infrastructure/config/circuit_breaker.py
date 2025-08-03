from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class CircuitBreakerOpen(RuntimeError):
    """Raised when operations are attempted on an open circuit."""


@dataclass
class CircuitBreaker:
    """Simple circuit breaker to guard operations.

    The breaker opens after ``failure_threshold`` consecutive failures and will
    reject further calls until ``recovery_timeout`` seconds have passed.
    Optionally a ``fallback`` callable can be provided which will be executed
    when the circuit is open instead of raising :class:`CircuitBreakerOpen`.
    """

    failure_threshold: int = 5
    recovery_timeout: float = 30.0
    fallback: Optional[Callable[[], T]] = None

    def __post_init__(self) -> None:
        self._failure_count = 0
        self._state = "closed"
        self._opened_at: Optional[float] = None

    @property
    def state(self) -> str:
        """Return current state, resetting if timeout elapsed."""
        if self._state == "open" and self._opened_at is not None:
            if time.monotonic() - self._opened_at >= self.recovery_timeout:
                self._state = "closed"
                self._failure_count = 0
                self._opened_at = None
        return self._state

    def call(self, func: Callable[[], T]) -> T:
        """Execute ``func`` honouring circuit state."""
        if self.state == "open":
            if self.fallback is not None:
                return self.fallback()
            raise CircuitBreakerOpen("circuit breaker is open")

        try:
            result = func()
        except Exception:
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = "open"
                self._opened_at = time.monotonic()
            raise
        else:
            self._failure_count = 0
            self._state = "closed"
            return result
