from __future__ import annotations

import random
import time
from dataclasses import dataclass
from typing import Callable, Optional, Protocol, TypeVar

from .database_exceptions import ConnectionRetryExhausted
from .protocols import (
    ConnectionRetryManagerProtocol,
    RetryConfigProtocol,
)

T = TypeVar("T")


@dataclass
class RetryConfig(RetryConfigProtocol):
    """Configuration for retry behaviour."""

    max_attempts: int = 3
    base_delay: float = 0.5
    jitter: bool = True
    backoff_factor: float = 2.0
    max_delay: float = 60.0


class RetryCallbacks(Protocol):
    def on_retry(self, attempt: int, delay: float) -> None: ...

    def on_success(self) -> None: ...

    def on_failure(self) -> None: ...


class ConnectionRetryManager(ConnectionRetryManagerProtocol):
    """Utility to retry a callable with exponential backoff."""

    def __init__(
        self,
        config: Optional[RetryConfig] = None,
        callbacks: Optional[RetryCallbacks] = None,
    ) -> None:
        self.config = config or RetryConfig()
        self.callbacks = callbacks

    def run_with_retry(self, func: Callable[[], T]) -> T:
        attempt = 1
        while True:
            try:
                result = func()
                if self.callbacks and hasattr(self.callbacks, "on_success"):
                    self.callbacks.on_success()
                return result
            except Exception as exc:
                if attempt >= self.config.max_attempts:
                    if self.callbacks and hasattr(self.callbacks, "on_failure"):
                        self.callbacks.on_failure()
                    raise ConnectionRetryExhausted(
                        "maximum retry attempts reached"
                    ) from exc
                delay = self.config.base_delay * (
                    self.config.backoff_factor ** (attempt - 1)
                )
                if self.config.jitter:
                    delay += random.uniform(0, self.config.base_delay)
                delay = min(delay, self.config.max_delay)
                if self.callbacks and hasattr(self.callbacks, "on_retry"):
                    self.callbacks.on_retry(attempt, delay)
                time.sleep(delay)
                attempt += 1
