from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta

__all__ = ["SecurityPatternsConfig"]


@dataclass
class SecurityPatternsConfig:
    """Configuration for adjustable threat detection thresholds."""

    travel_time_limit: timedelta = timedelta(minutes=1)
    attempts_window: timedelta = timedelta(minutes=5)
    attempts_threshold: int = 4
    visitor_window: timedelta = timedelta(minutes=5)
    no_exit_timeout: timedelta = timedelta(hours=12)
