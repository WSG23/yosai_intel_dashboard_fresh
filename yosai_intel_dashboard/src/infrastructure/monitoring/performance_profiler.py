from __future__ import annotations

"""Lightweight performance profiling utilities."""

import time
from contextlib import asynccontextmanager, contextmanager
from typing import Optional

import psutil

from yosai_intel_dashboard.src.core.performance import (
    MetricType,
    PerformanceThresholds,
    get_performance_monitor,
)


class PerformanceProfiler:
    """Record execution metrics and detect bottlenecks."""

    def __init__(self) -> None:
        self.monitor = get_performance_monitor()

    # ------------------------------------------------------------------
    @contextmanager
    def profile_endpoint(self, endpoint: str):
        """Profile CPU, memory, and time for a web endpoint."""
        proc = psutil.Process()
        start_cpu = proc.cpu_percent(interval=None)
        start_mem = proc.memory_info().rss / (1024 * 1024)
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            end_cpu = proc.cpu_percent(interval=None)
            end_mem = proc.memory_info().rss / (1024 * 1024)
            cpu_delta = max(0.0, end_cpu - start_cpu)
            mem_delta = end_mem - start_mem
            tags = {"endpoint": endpoint}
            self.monitor.record_metric(
                f"endpoint.{endpoint}.time",
                duration,
                MetricType.EXECUTION_TIME,
                duration=duration,
                tags=tags,
            )
            self.monitor.record_metric(
                f"endpoint.{endpoint}.cpu",
                cpu_delta,
                MetricType.CPU_USAGE,
                tags=tags,
            )
            self.monitor.record_metric(
                f"endpoint.{endpoint}.memory",
                mem_delta,
                MetricType.MEMORY_USAGE,
                tags=tags,
            )
            self._detect_bottleneck(
                f"endpoint.{endpoint}", duration, cpu_delta, mem_delta
            )

    # ------------------------------------------------------------------
    @asynccontextmanager
    async def track_db_query(self, query: str):
        """Measure execution time for a database query."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.monitor.record_metric(
                "db.query",
                duration,
                MetricType.DATABASE_QUERY,
                duration=duration,
                tags={"query": query},
            )
            if duration > PerformanceThresholds.SLOW_QUERY_SECONDS:
                self.monitor.logger.warning(
                    f"Slow DB query: {query} took {duration:.3f}s"
                )

    # ------------------------------------------------------------------
    @asynccontextmanager
    async def track_task(self, name: str):
        """Measure execution time for an async task."""
        start = time.perf_counter()
        try:
            yield
        finally:
            duration = time.perf_counter() - start
            self.monitor.record_metric(
                f"task.{name}",
                duration,
                MetricType.EXECUTION_TIME,
                duration=duration,
                tags={"task": name},
            )
            self._detect_bottleneck(f"task.{name}", duration)

    # ------------------------------------------------------------------
    def _detect_bottleneck(
        self,
        name: str,
        duration: float,
        cpu: Optional[float] = None,
        memory: Optional[float] = None,
    ) -> None:
        """Log potential bottlenecks based on thresholds."""
        if duration > PerformanceThresholds.SLOW_QUERY_SECONDS:
            self.monitor.logger.warning(
                f"Bottleneck detected: {name} took {duration:.3f}s"
            )
        if cpu is not None and cpu > 80.0:
            self.monitor.logger.warning(
                f"High CPU usage detected for {name}: {cpu:.1f}%"
            )
        if memory is not None and memory > 100.0:
            self.monitor.logger.warning(
                f"High memory usage detected for {name}: {memory:.1f}MB"
            )


__all__ = ["PerformanceProfiler"]
