from __future__ import annotations

"""Real-time UI metrics monitoring."""

import time
from dataclasses import dataclass, field
from typing import List, Optional

from core.performance import MetricType, get_performance_monitor


@dataclass
class FrameTiming:
    duration_ms: float
    timestamp: float = field(default_factory=time.time)


@dataclass
class CallbackTiming:
    name: str
    duration_ms: float
    timestamp: float = field(default_factory=time.time)


class RealTimeUIMonitor:
    """Record UI frame render times and callback durations."""

    def __init__(self) -> None:
        self.frame_times: List[FrameTiming] = []
        self.callback_times: List[CallbackTiming] = []
        self._frame_start: Optional[float] = None

    # ------------------------------------------------------------------
    def start_frame(self) -> None:
        """Mark the beginning of a frame."""
        self._frame_start = time.perf_counter()

    # ------------------------------------------------------------------
    def end_frame(self) -> None:
        """Record frame duration from the last :meth:`start_frame` call."""
        if self._frame_start is None:
            return
        duration = (time.perf_counter() - self._frame_start) * 1000.0
        self.record_frame_time(duration)
        self._frame_start = None

    # ------------------------------------------------------------------
    def record_frame_time(self, duration_ms: float) -> None:
        """Record a single frame render time in milliseconds."""
        self.frame_times.append(FrameTiming(duration_ms))
        get_performance_monitor().record_metric(
            "ui.frame_time_ms", duration_ms, MetricType.USER_INTERACTION
        )

    # ------------------------------------------------------------------
    def record_callback_duration(self, callback_name: str, duration_sec: float) -> None:
        """Record the execution time of a Dash callback."""
        duration_ms = duration_sec * 1000.0
        self.callback_times.append(CallbackTiming(callback_name, duration_ms))
        get_performance_monitor().record_metric(
            f"ui.callback.{callback_name}", duration_sec, MetricType.EXECUTION_TIME
        )


_ui_monitor: Optional[RealTimeUIMonitor] = None


def get_ui_monitor() -> RealTimeUIMonitor:
    """Return the global :class:`RealTimeUIMonitor` instance."""
    global _ui_monitor
    if _ui_monitor is None:
        _ui_monitor = RealTimeUIMonitor()
    return _ui_monitor


__all__ = ["RealTimeUIMonitor", "get_ui_monitor"]
