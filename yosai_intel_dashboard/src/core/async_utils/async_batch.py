from __future__ import annotations

import time
from collections.abc import AsyncIterable, Iterable
from typing import AsyncIterator, List, TypeVar

import psutil

from yosai_intel_dashboard.src.core.performance import (
    MetricType,
    get_performance_monitor,
)


T = TypeVar("T")

_profiler = PerformanceProfiler()


async def async_batch(
    source: AsyncIterable[T] | Iterable[T],
    size: int,
    *,
    queue_name: str = "default",
    task_type: str = "async_batch",
) -> AsyncIterator[List[T]]:
    """Yield lists of ``size`` items from ``source``.

    ``source`` can be an async iterable or regular iterable. Remaining
    items smaller than ``size`` are yielded at the end.
    """

    monitor = get_performance_monitor()
    tags = {"queue": queue_name, "task_type": task_type}
    start_time = time.time()
    start_mem = monitor.memory_usage_mb()
    start_cpu = psutil.cpu_percent()

    batch: List[T] = []
    try:

        if isinstance(source, AsyncIterable):
            async for item in source:
                batch.append(item)
                if len(batch) >= size:
                    yield batch
                    batch = []
        else:
            for item in source:
                batch.append(item)
                if len(batch) >= size:
                    yield batch
                    batch = []
        if batch:
            yield batch
    finally:
        duration = time.time() - start_time
        end_mem = monitor.memory_usage_mb()
        end_cpu = psutil.cpu_percent()
        monitor.record_metric(
            "async_batch",
            duration,
            MetricType.EXECUTION_TIME,
            tags=tags,
        )
        monitor.record_metric(
            "async_batch.memory_mb",
            end_mem - start_mem,
            MetricType.MEMORY_USAGE,
            tags=tags,
        )
        monitor.record_metric(
            "async_batch.cpu_percent",
            end_cpu - start_cpu,
            MetricType.CPU_USAGE,
            tags=tags,
        )
