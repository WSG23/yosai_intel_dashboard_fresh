from __future__ import annotations

"""Basic CPU usage monitoring helper."""

import logging

try:
    import psutil
except Exception:  # pragma: no cover - optional dependency
    psutil = None  # type: ignore


class CPUOptimizer:
    """Monitor CPU usage and warn when it exceeds a threshold."""

    def __init__(self, threshold_pct: float = 90.0) -> None:
        self.threshold_pct = threshold_pct
        self.logger = logging.getLogger(__name__)

    def cpu_percent(self) -> float:
        if not psutil:
            return 0.0
        try:
            return psutil.cpu_percent()
        except Exception:  # pragma: no cover - best effort
            return 0.0

    def check_usage(self) -> float:
        pct = self.cpu_percent()
        if pct > self.threshold_pct:
            self.logger.warning(
                f"CPU usage {pct:.1f}% exceeds threshold {self.threshold_pct:.1f}%"
            )
        return pct


__all__ = ["CPUOptimizer"]
