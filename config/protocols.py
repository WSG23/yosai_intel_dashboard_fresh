from __future__ import annotations

from typing import Callable, Protocol, TypeVar, Optional

T = TypeVar("T")

class RetryConfigProtocol(Protocol):
    max_attempts: int
    base_delay: float
    jitter: bool
    backoff_factor: float
    max_delay: float

class ConnectionRetryManagerProtocol(Protocol):
    def run_with_retry(self, func: Callable[[], T]) -> T: ...


__all__ = [
    "RetryConfigProtocol",
    "ConnectionRetryManagerProtocol",
]
