from __future__ import annotations

"""Simple repository layer for analytics data."""

from typing import Any, Optional

import pandas as pd


class AnalyticsDataRepository:
    """Fetch and store analytics data for the service layer."""

    def __init__(self, data: Optional[pd.DataFrame] = None) -> None:
        self._data = data
        self._last_results: Optional[dict[str, Any]] = None

    def get_data(self, criteria: Any) -> pd.DataFrame:
        """Return a DataFrame based on ``criteria``.

        If ``criteria`` is already a DataFrame it will be returned directly
        otherwise any preloaded data is returned.
        """
        if isinstance(criteria, pd.DataFrame):
            return criteria
        return self._data.copy() if self._data is not None else pd.DataFrame()

    def save_results(self, results: dict[str, Any]) -> None:
        """Persist the analysis results in memory."""
        self._last_results = dict(results)
