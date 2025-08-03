from __future__ import annotations

"""Utilities for analyzing performance trends over time."""

import logging
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional

import pandas as pd

from yosai_intel_dashboard.src.core.base_model import BaseModel
from yosai_intel_dashboard.src.core.performance import get_performance_monitor


class PerformanceAnalytics(BaseModel):
    """Simple analytics helpers using recorded metrics."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.monitor = get_performance_monitor()

    # ------------------------------------------------------------------
    def metrics_dataframe(self) -> pd.DataFrame:
        """Return all metrics as a :class:`~pandas.DataFrame`."""
        data = [
            {
                "timestamp": m.timestamp,
                "name": m.name,
                "value": m.value,
                "type": m.metric_type.value,
            }
            for m in self.monitor.metrics
        ]
        return pd.DataFrame(data)

    # ------------------------------------------------------------------
    def rolling_average(self, metric_name: str, window: int = 20) -> List[float]:
        """Calculate a rolling average for ``metric_name``."""
        values = [m.value for m in self.monitor.metrics if m.name == metric_name]
        if not values:
            return []
        averages: List[float] = []
        window_vals: deque[float] = deque()
        running_sum = 0.0
        for value in values:
            window_vals.append(value)
            running_sum += value
            if len(window_vals) > window:
                running_sum -= window_vals.popleft()
            averages.append(running_sum / len(window_vals))
        return averages

    # ------------------------------------------------------------------
    def summarize_by_type(self) -> Dict[str, float]:
        """Return average metric value grouped by type."""
        groups: Dict[str, List[float]] = defaultdict(list)
        for metric in self.monitor.metrics:
            groups[metric.metric_type.value].append(metric.value)
        return {key: sum(vals) / len(vals) for key, vals in groups.items() if vals}
