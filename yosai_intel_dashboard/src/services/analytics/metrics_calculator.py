"""Basic metrics calculator implementation."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from .protocols import MetricsCalculatorProtocol


class MetricsCalculator(MetricsCalculatorProtocol):
    """Simple metrics calculator stub."""

    def calculate_access_metrics(self, events: pd.DataFrame) -> Dict[str, float]:
        return {"events": float(len(events))}

    def calculate_security_metrics(self, events: pd.DataFrame) -> Dict[str, float]:
        return {"security_events": float(len(events))}

    def calculate_performance_metrics(self, data: pd.DataFrame) -> Dict[str, float]:
        return {"rows": float(len(data))}

    def calculate_trend_metrics(
        self, data: pd.DataFrame, window: str = "7d"
    ) -> Dict[str, Any]:
        return {"window": window, "count": len(data)}
