from __future__ import annotations

from dataclasses import dataclass
import functools
import logging
import os
import time
from typing import Any, Callable, Generator, Iterable

import psutil

logger = logging.getLogger(__name__)


@dataclass
class MemoryConfig:
    """Configuration for memory usage monitoring."""

    max_usage_mb: int = 1024
    check_interval: float = 1.0
    chunk_size: int = 1024 * 1024


class MemoryMonitor:
    """Monitors process RSS memory usage."""

    def __init__(self, config: MemoryConfig) -> None:
        self.config = config
        self.process = psutil.Process(os.getpid())
        self.last_check = 0.0

    def check(self) -> None:
        now = time.time()
        if now - self.last_check < self.config.check_interval:
            return
        self.last_check = now
        usage_mb = self.process.memory_info().rss / (1024**2)
        if usage_mb > self.config.max_usage_mb:
            raise MemoryError(
                f"Memory usage {usage_mb:.2f}MB exceeded limit {self.config.max_usage_mb}MB"
            )


class ChunkedDataProcessor:
    """Processes iterables while periodically checking memory."""

    def __init__(self, monitor: MemoryMonitor) -> None:
        self.monitor = monitor

    def process(self, data_iter: Iterable[Any]) -> Generator[Any, None, None]:
        for chunk in data_iter:
            self.monitor.check()
            yield chunk


class FileProcessor(ChunkedDataProcessor):
    """Reads files in chunks while monitoring memory usage."""

    def __init__(self, monitor: MemoryMonitor, chunk_size: int | None = None) -> None:
        super().__init__(monitor)
        self.chunk_size = chunk_size or monitor.config.chunk_size

    def read(self, path: str) -> Generator[bytes, None, None]:
        with open(path, "rb") as fh:
            while True:
                self.monitor.check()
                data = fh.read(self.chunk_size)
                if not data:
                    break
                yield data


def memory_safe(
    config: MemoryConfig,
) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to add memory monitoring to a function."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            monitor = MemoryMonitor(config)
            return func(*args, monitor=monitor, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "MemoryConfig",
    "MemoryMonitor",
    "ChunkedDataProcessor",
    "FileProcessor",
    "memory_safe",
]
