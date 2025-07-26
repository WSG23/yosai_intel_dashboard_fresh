from __future__ import annotations

"""Retry helpers for asynchronous functions."""

import asyncio
from typing import Awaitable, Callable, Iterable, TypeVar

T = TypeVar("T")


class AsyncRetry:
    """Retry an async callable with exponential backoff."""

    def __init__(
        self,
        attempts: int = 3,
        *,
        base_delay: float = 0.1,
        max_delay: float = 5.0,
        exceptions: Iterable[type[Exception]] = (Exception,),
    ) -> None:
        self.attempts = attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.exceptions = tuple(exceptions)

    async def __call__(self, func: Callable[..., Awaitable[T]], *args, **kwargs) -> T:
        delay = self.base_delay
        for attempt in range(1, self.attempts + 1):
            try:
                return await func(*args, **kwargs)
            except self.exceptions:
                if attempt == self.attempts:
                    raise
                await asyncio.sleep(min(delay, self.max_delay))
                delay *= 2
        raise RuntimeError("unreachable")

    def wrap(self, func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        async def wrapper(*args, **kwargs):
            return await self(func, *args, **kwargs)

        return wrapper


__all__ = ["AsyncRetry"]
