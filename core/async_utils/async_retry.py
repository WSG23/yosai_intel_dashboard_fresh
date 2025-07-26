from __future__ import annotations

import asyncio
import random
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

T = TypeVar("T")


async def _run_with_retry(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> T:
    attempt = 1
    while True:
        try:
            return await func()
        except Exception:
            if attempt >= max_attempts:
                raise
            delay = base_delay * (backoff_factor ** (attempt - 1))
            if jitter:
                delay += random.uniform(0, base_delay)
            delay = min(delay, max_delay)
            await asyncio.sleep(delay)
            attempt += 1


def async_retry(
    func: Callable[..., Awaitable[T]] | None = None,
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
) -> (
    Callable[..., Awaitable[T]]
    | Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]
):
    """Retry an async function with exponential backoff."""

    def decorator(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            async def call() -> T:
                return await fn(*args, **kwargs)

            return await _run_with_retry(
                call,
                max_attempts=max_attempts,
                base_delay=base_delay,
                backoff_factor=backoff_factor,
                max_delay=max_delay,
                jitter=jitter,
            )

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


__all__ = ["async_retry", "_run_with_retry"]
