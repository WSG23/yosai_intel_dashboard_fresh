"""Plugin performance tracking utilities."""

from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict
from typing import Any, Dict, List, Optional

from yosai_intel_dashboard.src.core.base_model import BaseModel
from yosai_intel_dashboard.src.core.protocols.plugin import PluginProtocol

from .manager import ThreadSafePluginManager


class PluginPerformanceManager(BaseModel):
    """Collect and analyze plugin performance metrics."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.metrics: Dict[str, List[Dict[str, float]]] = defaultdict(list)
        self.performance_thresholds: Dict[str, float] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self._metrics_lock = threading.RLock()

    # ------------------------------------------------------------------
    def record_plugin_metric(
        self, plugin_name: str, metric_type: str, value: float
    ) -> None:
        """Record a metric for ``plugin_name``."""
        with self._metrics_lock:
            self.metrics[plugin_name].append({metric_type: value})

    # ------------------------------------------------------------------
    def analyze_plugin_performance(self, plugin_name: str) -> Dict[str, Any]:
        """Return basic statistics for ``plugin_name``."""
        with self._metrics_lock:
            data = self.metrics.get(plugin_name, [])
        stats: Dict[str, Any] = {}
        for item in data:
            for key, val in item.items():
                stats.setdefault(key, []).append(val)
        summary = {m: sum(vals) / len(vals) for m, vals in stats.items() if vals}
        summary["samples"] = len(data)
        return summary

    # ------------------------------------------------------------------
    def detect_performance_issues(self) -> List[Dict[str, Any]]:
        """Detect plugins exceeding performance thresholds."""
        with self._metrics_lock:
            alerts = [
                {
                    "plugin": plugin,
                    "metric": metric,
                    "value": value,
                    "threshold": threshold,
                }
                for plugin, records in self.metrics.items()
                for record in records
                for metric, value in record.items()
                if (threshold := self.performance_thresholds.get(metric)) and value > threshold
            ]
            self.alert_history.extend(alerts)
        return alerts

    # ------------------------------------------------------------------
    def generate_performance_report(self, time_range: str = "1h") -> Dict[str, Any]:
        """Return a simple performance report."""
        report = {
            "generated_at": time.time(),
            "summary": {p: self.analyze_plugin_performance(p) for p in self.metrics},
            "alerts": self.detect_performance_issues(),
        }
        return report


# ---------------------------------------------------------------------------
# Enhanced manager
# ---------------------------------------------------------------------------


class EnhancedThreadSafePluginManager(ThreadSafePluginManager):
    """ThreadSafePluginManager with performance tracking."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.performance_manager = PluginPerformanceManager()
        self._start_monitoring()

    # ------------------------------------------------------------------
    def load_plugin(self, plugin: PluginProtocol) -> bool:  # type: ignore[override]
        plugin_name = self._get_plugin_name(plugin)
        start_time = time.time()
        memory_before = self._get_memory_usage()
        with self._lock:
            try:
                result = super().load_plugin(plugin)
                load_time = time.time() - start_time
                memory_after = self._get_memory_usage()
                memory_delta = memory_after - memory_before

                self.performance_manager.record_plugin_metric(
                    plugin_name, "load_time", load_time
                )
                self.performance_manager.record_plugin_metric(
                    plugin_name, "memory_usage", memory_delta
                )

                self._check_performance_thresholds(plugin_name, load_time, memory_delta)
                return result
            except Exception:
                error_time = time.time() - start_time
                self.performance_manager.record_plugin_metric(
                    plugin_name, "error_time", error_time
                )
                raise

    # ------------------------------------------------------------------
    def start_plugin(self, plugin_name: str) -> bool:
        start = time.time()
        result = super().plugins[plugin_name].start()
        duration = time.time() - start
        self.performance_manager.record_plugin_metric(
            plugin_name, "start_time", duration
        )
        self._check_performance_thresholds(plugin_name, duration, 0)
        return result

    # ------------------------------------------------------------------
    def health_check_plugin(self, plugin_name: str) -> Dict[str, Any]:
        start = time.time()
        result = super().plugins[plugin_name].health_check()
        duration = time.time() - start
        self.performance_manager.record_plugin_metric(
            plugin_name, "health_time", duration
        )
        self._check_performance_thresholds(plugin_name, duration, 0)
        return result

    # ------------------------------------------------------------------
    def get_plugin_performance_metrics(
        self, plugin_name: str | None = None
    ) -> Dict[str, Any]:
        if plugin_name:
            return self.performance_manager.analyze_plugin_performance(plugin_name)
        return {
            p: self.performance_manager.analyze_plugin_performance(p)
            for p in self.performance_manager.metrics
        }

    # ------------------------------------------------------------------
    def _check_performance_thresholds(
        self, plugin_name: str, load_time: float, memory_delta: float
    ) -> None:
        alerts = []
        lt = self.performance_manager.performance_thresholds.get("load_time")
        mem = self.performance_manager.performance_thresholds.get("memory_usage")
        if lt and load_time > lt:
            alerts.append(
                {"plugin": plugin_name, "metric": "load_time", "value": load_time}
            )
        if mem and memory_delta > mem:
            alerts.append(
                {"plugin": plugin_name, "metric": "memory_usage", "value": memory_delta}
            )
        self.performance_manager.alert_history.extend(alerts)

    # ------------------------------------------------------------------
    def _get_memory_usage(self) -> float:
        import psutil

        proc = psutil.Process()
        return proc.memory_info().rss / (1024 * 1024)

    # ------------------------------------------------------------------
    def _start_monitoring(self) -> None:
        import psutil

        self._perf_monitor_active = True
        self._monitor_interval = 60

        proc = psutil.Process()

        def monitor_loop() -> None:
            while self._perf_monitor_active:
                cpu = proc.cpu_percent(interval=None)
                mem = proc.memory_info().rss / (1024 * 1024)

                self.performance_manager.record_plugin_metric(
                    "system", "cpu_usage", cpu
                )
                self.performance_manager.record_plugin_metric(
                    "system", "memory_usage", mem
                )

                thresholds = self.performance_manager.performance_thresholds
                if thresholds.get("cpu_usage") and cpu > thresholds["cpu_usage"]:
                    self.performance_manager.alert_history.append(
                        {"plugin": "system", "metric": "cpu_usage", "value": cpu}
                    )
                if thresholds.get("memory_usage") and mem > thresholds["memory_usage"]:
                    self.performance_manager.alert_history.append(
                        {
                            "plugin": "system",
                            "metric": "memory_usage",
                            "value": mem,
                        }
                    )

                time.sleep(self._monitor_interval)

        self._perf_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._perf_thread.start()
