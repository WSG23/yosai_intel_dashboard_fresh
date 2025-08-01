from __future__ import annotations

"""Real time performance tracker for web vitals and callbacks."""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

import psutil

from yosai_intel_dashboard.src.core.base_model import BaseModel
from yosai_intel_dashboard.src.core.performance import MetricType, get_performance_monitor


@dataclass
class WebVital:
    """Data structure for a single Core Web Vital."""

    name: str
    value: float
    timestamp: datetime = field(default_factory=datetime.utcnow)


class RealTimePerformanceTracker(BaseModel):
    """Capture metrics related to the live user experience."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.web_vitals: Dict[str, WebVital] = {}

    # ------------------------------------------------------------------
    def record_core_web_vitals(self, **metrics: float) -> None:
        """Record values for LCP, FID, CLS, FCP, TTFB, etc."""
        monitor = get_performance_monitor()
        for name, value in metrics.items():
            self.web_vitals[name] = WebVital(name, value)
            monitor.record_metric(
                f"web_vital.{name}", value, MetricType.USER_INTERACTION
            )

    # ------------------------------------------------------------------
    def record_upload_speed(self, file_size_mb: float, duration_sec: float) -> None:
        """Track upload throughput in MB/s."""
        speed = file_size_mb / duration_sec if duration_sec > 0 else 0.0
        get_performance_monitor().record_metric(
            "upload.speed_mb_s",
            speed,
            MetricType.FILE_PROCESSING,
            metadata={"file_size_mb": file_size_mb, "duration_sec": duration_sec},
        )

    # ------------------------------------------------------------------
    def record_callback_duration(self, callback_name: str, duration_sec: float) -> None:
        """Record execution time for Dash callbacks."""
        get_performance_monitor().record_metric(
            f"callback.{callback_name}.duration",
            duration_sec,
            MetricType.EXECUTION_TIME,
        )

    # ------------------------------------------------------------------
    def record_memory_usage(self) -> None:
        """Capture current process memory usage."""
        mem = psutil.Process().memory_info().rss / (1024 * 1024)
        get_performance_monitor().record_metric(
            "system.memory_used_mb", mem, MetricType.MEMORY_USAGE
        )
