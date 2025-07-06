from __future__ import annotations

"""Utilities for analyzing performance trends over time."""

from collections import defaultdict
from typing import Dict, List

import pandas as pd

from core.performance import PerformanceMetric, get_performance_monitor


class PerformanceAnalytics:
    """Simple analytics helpers using recorded metrics."""

    def __init__(self) -> None:
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
        return pd.Series(values).rolling(window=window, min_periods=1).mean().tolist()

    # ------------------------------------------------------------------
    def summarize_by_type(self) -> Dict[str, float]:
        """Return average metric value grouped by type."""
        groups: Dict[str, List[float]] = defaultdict(list)
        for metric in self.monitor.metrics:
            groups[metric.metric_type.value].append(metric.value)
        return {key: sum(vals) / len(vals) for key, vals in groups.items() if vals}
