from __future__ import annotations

"""Simple retry helper used by pooled connections.

The :class:`RetryStrategy` encapsulates retry logic with exponential
backoff suitable for dealing with transient failures such as temporary
network issues or database lock timeouts.  The delay doubles after each
failed attempt which gives the remote service time to recover.  The
strategy is intentionally lightweight – callers can override the
default number of ``attempts`` and initial ``backoff`` delay per call to
match the characteristics of the operation being performed.

Example
-------

>>> retry = RetryStrategy(attempts=5, backoff=0.2)
>>> retry.run(unreliable_operation)

The above will attempt ``unreliable_operation`` up to five times,
sleeping for ``0.2``, ``0.4``, ``0.8`` ... seconds between retries.
"""

from dataclasses import dataclass
import time
from typing import Callable, TypeVar, Any

T = TypeVar("T")


@dataclass
class RetryStrategy:
    """Retry callable with exponential backoff."""

    attempts: int = 3
    backoff: float = 0.1

    def run(
        self,
        func: Callable[[], T],
        *,
        attempts: int | None = None,
        backoff: float | None = None,
    ) -> T:
        """Run ``func`` applying the retry strategy.

        Parameters
        ----------
        func:
            Zero-argument callable to execute.
        attempts:
            Optional override for the number of attempts.
        backoff:
            Optional override for the initial backoff delay.
        """

        max_attempts = attempts if attempts is not None else self.attempts
        delay = backoff if backoff is not None else self.backoff

        if max_attempts <= 0:
            raise ValueError("attempts must be positive")

        for attempt in range(max_attempts):
            try:
                return func()
            except Exception:
                if attempt == max_attempts - 1:
                    raise
                time.sleep(delay)
                delay *= 2


__all__ = ["RetryStrategy"]
