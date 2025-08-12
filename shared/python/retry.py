from __future__ import annotations

import asyncio
import random
import time
from typing import Any, Callable, Iterable, Type


class RetryError(RuntimeError):
    pass


def _sleep(seconds: float) -> None:
    time.sleep(seconds)


def _ajitter(base: float, jitter: float = 0.2) -> float:
    return max(0.0, base * (1.0 + random.uniform(-jitter, jitter)))


def retry(
    fn: Callable[[], Any],
    *,
    attempts: int = 3,
    base_delay: float = 0.2,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
) -> Any:
    last = None
    for i in range(1, attempts + 1):
        try:
            return fn()
        except exceptions as e:
            last = e
            if i == attempts:
                break
            _sleep(_ajitter(base_delay * (2 ** (i - 1))))
    raise RetryError(str(last)) from last


async def aretry(
    fn: Callable[[], Any],
    *,
    attempts: int = 3,
    base_delay: float = 0.2,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
) -> Any:
    last = None
    for i in range(1, attempts + 1):
        try:
            res = fn()
            if asyncio.iscoroutine(res):
                return await res
            return res
        except exceptions as e:
            last = e
            if i == attempts:
                break
            await asyncio.sleep(_ajitter(base_delay * (2 ** (i - 1))))
    raise RetryError(str(last)) from last
