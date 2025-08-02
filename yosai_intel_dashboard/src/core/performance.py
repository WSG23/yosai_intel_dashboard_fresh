# core/performance.py
"""
Performance optimization and monitoring system
Inspired by Apple's Instruments and performance measurement tools
"""
from __future__ import annotations

import functools
import logging
import math
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from types import SimpleNamespace
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Tuple,
)

import numpy as np
import pandas as pd
import psutil
import yaml
from prometheus_client import REGISTRY, Counter
from prometheus_client.core import CollectorRegistry

from monitoring.request_metrics import async_task_duration
from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import (
    dynamic_config,
)

try:  # pragma: no cover - optional dependency
    from yosai_intel_dashboard.src.services.query_optimizer import QueryOptimizer
except Exception:  # pragma: no cover - optional dependency
    QueryOptimizer = None  # type: ignore

if TYPE_CHECKING:  # pragma: no cover - imported for type hints only
    from yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor import (
        ModelMetrics,
    )
    from yosai_intel_dashboard.src.core.monitoring.user_experience_metrics import (
        AlertDispatcher,
    )

from .base_model import BaseModel
from .cpu_optimizer import CPUOptimizer
from .memory_manager import MemoryManager

if "performance_budget_violation_total" not in REGISTRY._names_to_collectors:
    performance_budget_violation_total = Counter(
        "performance_budget_violation_total",
        "Total performance budget violations",
    )
else:  # pragma: no cover - defensive in tests
    performance_budget_violation_total = Counter(
        "performance_budget_violation_total",
        "Total performance budget violations",
        registry=CollectorRegistry(),
    )


def _load_budgets(path: Optional[str]) -> Dict[str, float]:
    """Return performance budgets defined in YAML ``path``.

    Missing files yield an empty mapping.
    """
    if not path:
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return {}

    budgets: Dict[str, float] = {}
    for key, value in data.items():
        try:
            budgets[key] = float(np.asarray(value, dtype=float))
        except (TypeError, ValueError):
            continue
    return budgets


def _check_budget(
    name: str,
    value: float,
    budgets: Mapping[str, float],
    dispatcher: Optional[AlertDispatcher] = None,
) -> None:
    """Increment violation counter and alert if ``value`` exceeds budget."""
    threshold = budgets.get(name)
    if threshold is not None and value > threshold:
        performance_budget_violation_total.inc()
        if dispatcher is not None:
            dispatcher.send_alert(
                f"{name} exceeded budget: {value:.2f} > {threshold:.2f}"
            )


class PerformanceThresholds:
    """Common performance threshold values."""

    SLOW_QUERY_SECONDS = 1.0
    CACHE_TIMEOUT_SECONDS = 300
    MAX_SLOW_QUERIES = 100


class MetricType(Enum):
    """Types of performance metrics"""

    EXECUTION_TIME = "execution_time"
    MEMORY_USAGE = "memory_usage"
    CPU_USAGE = "cpu_usage"
    DATABASE_QUERY = "database_query"
    FILE_PROCESSING = "file_processing"
    API_CALL = "api_call"
    USER_INTERACTION = "user_interaction"
    DEPRECATED_USAGE = "deprecated_usage"


@dataclass
class PerformanceMetric:
    """Individual performance metric"""

    name: str
    metric_type: MetricType
    value: float
    timestamp: datetime
    duration: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class PerformanceSnapshot:
    """System performance snapshot"""

    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    active_threads: int
    active_connections: int = 0


class PerformanceMonitor:
    """
    Comprehensive performance monitoring system
    Tracks execution times, resource usage, and system health
    """

    def __init__(self, max_metrics: int = 10000):
        self.metrics: deque = deque(maxlen=max_metrics)
        self.snapshots: deque = deque(maxlen=1000)
        self.active_timers: Dict[str, float] = {}
        self.aggregated_metrics: Dict[str, List[float]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
        self._lock = threading.Lock()
        self.memory_threshold_mb = getattr(
            dynamic_config.performance, "memory_usage_threshold_mb", 1024
        )
        self.cpu = CPUOptimizer()
        self.memory = MemoryManager(self.memory_threshold_mb)

        budget_file = getattr(dynamic_config.performance, "budget_file", None)
        self.budgets = _load_budgets(budget_file)
        self.dispatcher: Optional[AlertDispatcher] = None

        # Start background monitoring
        self._monitoring_active = True
        self._monitor_thread = threading.Thread(
            target=self._background_monitor, daemon=True
        )
        self._monitor_thread.start()

    def record_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType = MetricType.EXECUTION_TIME,
        duration: Optional[float] = None,
        metadata: Dict[str, Any] = None,
        tags: Dict[str, str] = None,
    ) -> None:
        """Record a performance metric"""
        metric = PerformanceMetric(
            name=name,
            metric_type=metric_type,
            value=value,
            timestamp=datetime.now(),
            duration=duration,
            metadata=metadata or {},
            tags=tags or {},
        )

        with self._lock:
            self.metrics.append(metric)
            self.aggregated_metrics[name].append(value)

            # Keep only recent aggregated metrics
            if len(self.aggregated_metrics[name]) > 1000:
                self.aggregated_metrics[name] = self.aggregated_metrics[name][-1000:]

            if self.budgets:
                _check_budget(name.split(".")[0], value, self.budgets, self.dispatcher)

    def start_timer(self, name: str) -> None:
        """Start a named timer"""
        self.active_timers[name] = time.time()

    def end_timer(
        self,
        name: str,
        metric_type: MetricType = MetricType.EXECUTION_TIME,
        metadata: Dict[str, Any] = None,
        tags: Dict[str, str] = None,
    ) -> float:
        """End a named timer and record the duration"""
        if name not in self.active_timers:
            self.logger.warning(f"Timer {name} not found")
            return 0.0

        duration = time.time() - self.active_timers.pop(name)

        self.record_metric(
            name=name,
            value=duration,
            metric_type=metric_type,
            duration=duration,
            metadata=metadata,
            tags=tags,
        )

        return duration

    def get_system_snapshot(self) -> PerformanceSnapshot:
        """Get current system performance snapshot"""
        return PerformanceSnapshot(
            timestamp=datetime.now(),
            cpu_percent=psutil.cpu_percent(),
            memory_percent=psutil.virtual_memory().percent,
            memory_used_mb=psutil.virtual_memory().used / (1024 * 1024),
            active_threads=threading.active_count(),
        )

    def memory_usage_mb(self) -> float:
        """Return current process memory usage in MB."""
        return psutil.Process().memory_info().rss / (1024 * 1024)

    def throttle_if_needed(self) -> None:
        """Abort or slow down processing if memory usage is high."""
        usage = self.memory_usage_mb()
        if usage > self.memory_threshold_mb:
            raise MemoryError(
                f"Memory limit exceeded: {usage:.1f}MB > {self.memory_threshold_mb}MB"
            )
        if usage > self.memory_threshold_mb * 0.9:
            time.sleep(0.01)

    def _background_monitor(self) -> None:
        """Background thread for system monitoring"""
        while self._monitoring_active:
            try:
                snapshot = self.get_system_snapshot()
                self.snapshots.append(snapshot)

                # Record system metrics
                self.record_metric(
                    "system.cpu_percent", snapshot.cpu_percent, MetricType.CPU_USAGE
                )
                self.record_metric(
                    "system.memory_percent",
                    snapshot.memory_percent,
                    MetricType.MEMORY_USAGE,
                )
                self.record_metric(
                    "system.memory_used_mb",
                    snapshot.memory_used_mb,
                    MetricType.MEMORY_USAGE,
                )

                time.sleep(30)  # Monitor every 30 seconds

            except Exception as e:
                self.logger.error(f"Background monitoring error: {e}")
                time.sleep(60)  # Wait longer on error

    def get_metrics_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get performance metrics summary"""
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_metrics = [m for m in self.metrics if m.timestamp >= cutoff]

        if not recent_metrics:
            return {"total_metrics": 0}

        # Group by metric type
        by_type = defaultdict(list)
        for metric in recent_metrics:
            by_type[metric.metric_type].append(metric.value)

        # Calculate statistics
        summary = {"total_metrics": len(recent_metrics)}

        for metric_type, values in by_type.items():
            summary[metric_type.value] = {
                "count": len(values),
                "mean": sum(values) / len(values),
                "min": min(values),
                "max": max(values),
                "p95": self._percentile(values, 95),
                "p99": self._percentile(values, 99),
            }

        return summary

    def get_slow_operations(
        self,
        threshold: float = PerformanceThresholds.SLOW_QUERY_SECONDS,
        hours: int = 24,
    ) -> List[Dict[str, Any]]:
        """Get operations that exceeded threshold"""
        cutoff = datetime.now() - timedelta(hours=hours)

        slow_ops = []
        for metric in self.metrics:
            if (
                metric.timestamp >= cutoff
                and metric.metric_type == MetricType.EXECUTION_TIME
                and metric.value > threshold
            ):
                slow_ops.append(
                    {
                        "name": metric.name,
                        "duration": metric.value,
                        "timestamp": metric.timestamp,
                        "metadata": metric.metadata,
                    }
                )

        return sorted(slow_ops, key=lambda x: x["duration"], reverse=True)

    def get_deprecation_counts(self, hours: int = 24) -> Dict[str, int]:
        """Return how often deprecated functions were called in the last ``hours``."""
        cutoff = datetime.now() - timedelta(hours=hours)
        counts: Dict[str, int] = defaultdict(int)
        for metric in self.metrics:
            if (
                metric.timestamp >= cutoff
                and metric.metric_type == MetricType.DEPRECATED_USAGE
            ):
                counts[metric.name] += 1
        return dict(counts)

    def get_profiler_report(self, session_name: str) -> Dict[str, Any]:
        """Aggregate profiler metrics for a session."""
        prefix = f"profiler.{session_name}."
        report: Dict[str, Any] = {"session": session_name, "functions": {}}
        total_time = 0.0

        with self._lock:
            for metric_name, values in self.aggregated_metrics.items():
                if metric_name.startswith(prefix):
                    func_name = metric_name[len(prefix) :]
                    total = sum(values)
                    total_time += total
                    report["functions"][func_name] = {
                        "calls": len(values),
                        "total_time": total,
                        "average_time": total / len(values),
                        "min_time": min(values),
                        "max_time": max(values),
                    }

        report["total_time"] = total_time
        report["function_count"] = sum(
            metrics["calls"] for metrics in report["functions"].values()
        )
        return report

    # ------------------------------------------------------------------
    def detect_model_drift(
        self,
        metrics: Mapping[str, float],
        baseline: Mapping[str, float],
        *,
        drift_threshold: float = 0.05,
        fields: Iterable[str] = ("accuracy", "precision", "recall"),
    ) -> bool:
        """Return ``True`` if ``metrics`` deviate from ``baseline`` by more than ``drift_threshold``.

        Parameters
        ----------
        metrics:
            Mapping of metric names to current values.
        baseline:
            Mapping of metric names to baseline values.
        drift_threshold:
            Relative difference above which drift is flagged.
        fields:
            Metric keys to compare. Defaults to ``("accuracy", "precision", "recall")``.
        """

        for metric_key in fields:
            if metric_key not in metrics or metric_key not in baseline:
                continue
            current = metrics[metric_key]
            base = baseline[metric_key]
            diff = abs(current - base) if base == 0 else abs(current - base) / base
            if diff - drift_threshold > 1e-9:

                return True
        return False

    def _percentile(self, values: List[float], percentile: int) -> float:
        """Calculate percentile of values"""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def stop_monitoring(self) -> None:
        """Stop background monitoring"""
        self._monitoring_active = False
        if self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=5)


# Lazy-loaded global performance monitor instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Return the singleton performance monitor, creating it if necessary."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


def measure_performance(
    name: str = None,
    metric_type: MetricType = MetricType.EXECUTION_TIME,
    threshold: float = None,
    tags: Dict[str, str] = None,
):
    """Decorator to measure function performance"""

    def decorator(func: Callable) -> Callable:
        metric_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

            try:
                result = func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                memory_delta = end_memory - start_memory

                # Record performance metrics
                get_performance_monitor().record_metric(
                    name=metric_name,
                    value=duration,
                    metric_type=metric_type,
                    duration=duration,
                    metadata={
                        "success": success,
                        "error": error,
                        "memory_delta_mb": memory_delta,
                        "args_count": len(args),
                        "kwargs_count": len(kwargs),
                    },
                    tags=tags,
                )

                # Log slow operations
                if threshold and duration > threshold:
                    get_performance_monitor().logger.warning(
                        f"Slow operation: {metric_name} took {duration:.3f}s "
                        f"(threshold: {threshold}s)"
                    )

            return result

        return wrapper

    return decorator


def measure_async_performance(
    name: str = None,
    metric_type: MetricType = MetricType.EXECUTION_TIME,
    threshold: float = None,
    tags: Dict[str, str] = None,
):
    """Decorator to measure async function performance"""

    def decorator(func: Callable) -> Callable:
        metric_name = name or f"{func.__module__}.{func.__name__}"

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB

            try:
                result = await func(*args, **kwargs)
                success = True
                error = None
            except Exception as e:
                success = False
                error = str(e)
                raise
            finally:
                duration = time.time() - start_time
                end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
                memory_delta = end_memory - start_memory

                # Record performance metrics
                get_performance_monitor().record_metric(
                    name=metric_name,
                    value=duration,
                    metric_type=metric_type,
                    duration=duration,
                    metadata={
                        "success": success,
                        "error": error,
                        "memory_delta_mb": memory_delta,
                        "async": True,
                    },
                    tags=tags,
                )

                # Log slow operations
                if threshold and duration > threshold:
                    get_performance_monitor().logger.warning(
                        f"Slow async operation: {metric_name} took {duration:.3f}s"
                    )

            return result

        return wrapper

    return decorator


class PerformanceProfiler(BaseModel):
    """
    Code profiler for detailed performance analysis
    Similar to Apple's Time Profiler instrument
    """

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.profile_data: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
        self.active_profiles: Dict[str, float] = {}
        # Track N+1 query occurrences keyed by endpoint
        self.n_plus_one_queries: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    def start_profiling(self, session_name: str) -> None:
        """Start a profiling session"""
        if not dynamic_config.performance.profiling_enabled:
            return
        self.active_profiles[session_name] = time.time()

    def end_profiling(self, session_name: str) -> Optional[float]:
        """End profiling session and return duration"""
        if (
            not dynamic_config.performance.profiling_enabled
            or session_name not in self.active_profiles
        ):
            return None

        duration = time.time() - self.active_profiles.pop(session_name)
        self.profile_data[session_name].append(("session", duration))
        get_performance_monitor().record_metric(
            f"profiler.{session_name}.session",
            duration,
            MetricType.EXECUTION_TIME,
            tags={"session": session_name},
        )
        return duration

    def profile_function(
        self, session_name: str, func_name: str, duration: float
    ) -> None:
        """Record function profiling data"""
        if not dynamic_config.performance.profiling_enabled:
            return
        self.profile_data[session_name].append((func_name, duration))
        get_performance_monitor().record_metric(
            f"profiler.{session_name}.{func_name}",
            duration,
            MetricType.EXECUTION_TIME,
            tags={"session": session_name, "function": func_name},
        )

    def get_profile_report(self, session_name: str) -> Dict[str, Any]:
        """Get profiling report for session"""
        if not dynamic_config.performance.profiling_enabled:
            return {}
        return get_performance_monitor().get_profiler_report(session_name)

    def record_n_plus_one(self, endpoint: str, query: str, stacks: List[str]) -> None:
        """Record an N+1 query occurrence for an endpoint."""
        self.n_plus_one_queries[endpoint].append(
            {"query": query, "stacks": stacks, "timestamp": datetime.now()}
        )

    def get_n_plus_one_queries(self) -> Dict[str, List[Dict[str, Any]]]:
        """Return recorded N+1 query occurrences."""
        return self.n_plus_one_queries


class CacheMonitor(BaseModel):
    """Monitor cache performance and hit rates"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.cache_stats: Dict[str, Dict[str, int]] = defaultdict(
            lambda: {"hits": 0, "misses": 0}
        )
        self.cache_sizes: Dict[str, int] = {}
        self._caches: Dict[str, Any] = {}

    def record_cache_hit(self, cache_name: str) -> None:
        """Record cache hit"""
        self.cache_stats[cache_name]["hits"] += 1
        get_performance_monitor().record_metric(
            f"cache.{cache_name}.hit",
            1,
            MetricType.API_CALL,
            tags={"cache_name": cache_name, "result": "hit"},
        )

    def record_cache_miss(self, cache_name: str) -> None:
        """Record cache miss"""
        self.cache_stats[cache_name]["misses"] += 1
        get_performance_monitor().record_metric(
            f"cache.{cache_name}.miss",
            1,
            MetricType.API_CALL,
            tags={"cache_name": cache_name, "result": "miss"},
        )

    def get_cache_hit_rate(self, cache_name: str) -> float:
        """Get cache hit rate percentage"""
        stats = self.cache_stats[cache_name]
        total = stats["hits"] + stats["misses"]
        return (stats["hits"] / total * 100) if total > 0 else 0.0

    def register_cache(self, cache_name: str, cache: Any) -> None:
        """Register a cache providing a ``stats`` method."""
        self._caches[cache_name] = cache

    def get_all_cache_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all caches"""
        result = {}
        for name, cache in self._caches.items():
            if hasattr(cache, "stats"):
                result[name] = cache.stats()
        for cache_name, stats in self.cache_stats.items():
            if cache_name in result:
                continue
            total = stats["hits"] + stats["misses"]
            result[cache_name] = {
                "hits": stats["hits"],
                "misses": stats["misses"],
                "total_requests": total,
                "hit_rate_percent": self.get_cache_hit_rate(cache_name),
                "size": self.cache_sizes.get(cache_name, 0),
            }
        return result


class DatabaseQueryMonitor(BaseModel):
    """Monitor database query performance"""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.slow_queries: List[Dict[str, Any]] = []
        self.query_stats: Dict[str, List[float]] = defaultdict(list)
        # Query optimizer used for explain plans and N+1 detection
        if QueryOptimizer is not None:
            self.optimizer = QueryOptimizer(self.db)
        else:  # pragma: no cover - fallback for tests
            self.optimizer = SimpleNamespace(
                track_query=lambda *_, **__: False,
                analyze_query=lambda *_, **__: {},
            )

    def record_query(
        self,
        query: str,
        duration: float,
        rows_affected: int = 0,
        database: str = "default",
    ) -> None:
        """Record database query performance"""
        # Normalize query for tracking (remove specific values)
        normalized_query = self._normalize_query(query)

        self.query_stats[normalized_query].append(duration)
        # Track for N+1 issues
        if self.optimizer.track_query(query):
            get_performance_monitor().record_metric(
                "database.query.n_plus_one",
                1,
                MetricType.DATABASE_QUERY,
                metadata={"query": query[:200], "database": database},
            )

        # Record as performance metric
        get_performance_monitor().record_metric(
            f"database.query.{normalized_query[:50]}",
            duration,
            MetricType.DATABASE_QUERY,
            metadata={
                "query": query[:200],  # Truncate for storage
                "rows_affected": rows_affected,
                "database": database,
            },
        )

        # Track slow queries
        if duration > PerformanceThresholds.SLOW_QUERY_SECONDS:
            analysis = self.optimizer.analyze_query(query)
            self.slow_queries.append(
                {
                    "query": query,
                    "duration": duration,
                    "timestamp": datetime.now(),
                    "rows_affected": rows_affected,
                    "database": database,
                    "plan": analysis.get("plan"),
                    "recommendations": analysis.get("recommendations"),
                }
            )

            # Keep only recent slow queries
            if len(self.slow_queries) > PerformanceThresholds.MAX_SLOW_QUERIES:
                self.slow_queries = self.slow_queries[
                    -PerformanceThresholds.MAX_SLOW_QUERIES :
                ]

    def _normalize_query(self, query: str) -> str:
        """Normalize query for pattern tracking"""
        import re

        # Remove specific values, keep structure
        normalized = re.sub(r"'[^']*'", "'?'", query)
        normalized = re.sub(r"\b\d+\b", "?", normalized)
        normalized = re.sub(r"\s+", " ", normalized).strip()
        return normalized[:100]  # Limit length

    def get_slow_queries(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get slowest recent queries"""
        return sorted(self.slow_queries, key=lambda x: x["duration"], reverse=True)[
            :limit
        ]

    def get_query_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Get query pattern statistics"""
        patterns = {}
        for pattern, durations in self.query_stats.items():
            patterns[pattern] = {
                "count": len(durations),
                "avg_duration": sum(durations) / len(durations),
                "max_duration": max(durations),
                "min_duration": min(durations),
            }
        return patterns


# Global instances
profiler = PerformanceProfiler()
cache_monitor = CacheMonitor()
db_monitor = DatabaseQueryMonitor()


# Context managers for easy performance tracking
class PerformanceContext:
    """Context manager for performance tracking"""

    def __init__(self, name: str, metric_type: MetricType = MetricType.EXECUTION_TIME):
        self.name = name
        self.metric_type = metric_type
        self.start_time: Optional[float] = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            get_performance_monitor().record_metric(
                self.name,
                duration,
                self.metric_type,
                metadata={"success": exc_type is None},
            )


class DatabaseQueryContext:
    """Context manager for database query tracking"""

    def __init__(self, query: str, database: str = "default"):
        self.query = query
        self.database = database
        self.start_time: Optional[float] = None
        self.rows_affected = 0

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            db_monitor.record_query(
                self.query, duration, self.rows_affected, self.database
            )

    def set_rows_affected(self, count: int) -> None:
        """Set number of rows affected by query"""
        self.rows_affected = count


# Utility functions for performance tracking
def get_performance_dashboard() -> Dict[str, Any]:
    """Get comprehensive performance dashboard data"""
    return {
        "timestamp": datetime.now(),
        "system_snapshot": get_performance_monitor().get_system_snapshot().__dict__,
        "metrics_summary": get_performance_monitor().get_metrics_summary(),
        "slow_operations": get_performance_monitor().get_slow_operations(),
        "cache_stats": cache_monitor.get_all_cache_stats(),
        "slow_queries": db_monitor.get_slow_queries(),
        "query_patterns": db_monitor.get_query_patterns(),
    }


def export_performance_report(hours: int = 24) -> pd.DataFrame:
    """Export performance data as DataFrame for analysis"""
    metrics = []
    cutoff = datetime.now() - timedelta(hours=hours)

    for metric in get_performance_monitor().metrics:
        if metric.timestamp >= cutoff:
            metrics.append(
                {
                    "timestamp": metric.timestamp,
                    "name": metric.name,
                    "type": metric.metric_type.value,
                    "value": metric.value,
                    "duration": metric.duration,
                    **metric.metadata,
                }
            )

    return pd.DataFrame(metrics)
