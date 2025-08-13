from __future__ import annotations

"""Simplified analytics service with explicit type annotations for mypy."""

from typing import Any, Dict

class AnalyticsService:
    """Minimal service returning placeholder analytics data."""

    def __init__(self) -> None:
        self._metrics: Dict[str, Any] = {}

    def get_analytics(self, source: str) -> Dict[str, Any]:
        """Return dummy analytics information for ``source``."""
        return {"source": source, "status": "ok"}

    def process_dataframe(self, df: Any) -> Dict[str, Any]:
        """Return the number of rows in ``df`` if available."""
        rows = getattr(df, "shape", (0,))[0]
        return {"rows": rows}

    def get_metrics(self) -> Dict[str, Any]:
        """Return collected metrics."""
        return dict(self._metrics)


def get_analytics_service() -> AnalyticsService:
    """Provide a default :class:`AnalyticsService` instance."""
    return AnalyticsService()
