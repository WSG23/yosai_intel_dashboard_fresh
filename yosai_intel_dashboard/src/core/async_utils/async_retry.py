from __future__ import annotations

import asyncio
import random
import time
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

import psutil

from yosai_intel_dashboard.src.core.performance import (
    MetricType,
    get_performance_monitor,
)

T = TypeVar("T")


async def _run_with_retry(
    func: Callable[[], Awaitable[T]],
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    queue_name: str = "default",
    task_type: str = "async_retry",
) -> T:
    monitor = get_performance_monitor()
    tags = {"queue": queue_name, "task_type": task_type}
    start_time = time.time()
    start_mem = monitor.memory_usage_mb()
    start_cpu = psutil.cpu_percent()
    attempt = 1
    try:
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
    finally:
        duration = time.time() - start_time
        end_mem = monitor.memory_usage_mb()
        end_cpu = psutil.cpu_percent()
        monitor.record_metric(
            "async_retry",
            duration,
            MetricType.EXECUTION_TIME,
            tags=tags,
        )
        monitor.record_metric(
            "async_retry.memory_mb",
            end_mem - start_mem,
            MetricType.MEMORY_USAGE,
            tags=tags,
        )
        monitor.record_metric(
            "async_retry.cpu_percent",
            end_cpu - start_cpu,
            MetricType.CPU_USAGE,
            tags=tags,
        )


def async_retry(
    func: Callable[..., Awaitable[T]] | None = None,
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    queue_name: str = "default",
    task_type: str | None = None,
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
                queue_name=queue_name,
                task_type=task_type or fn.__name__,
            )

        return wrapper

    if func is not None:
        return decorator(func)

    return decorator


__all__ = ["async_retry", "_run_with_retry"]
