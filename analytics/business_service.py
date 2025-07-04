from __future__ import annotations

"""Business logic for analytics processing."""

from typing import Any, Dict

import pandas as pd

from .data_repository import AnalyticsDataRepository


class AnalyticsBusinessService:
    """Perform analytics calculations using a data repository."""

    def __init__(self, repository: AnalyticsDataRepository) -> None:
        self.repository = repository

    # ------------------------------------------------------------------
    def run_analysis(self, criteria: Any) -> Dict[str, Any]:
        """Retrieve data using ``criteria`` and return analysis results."""
        df = self.repository.get_data(criteria)
        results = self._analyze_data(df)
        self.repository.save_results(results)
        return results

    # ------------------------------------------------------------------
    def _analyze_data(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze the provided dataframe and return summary stats."""
        total_events = len(df)
        unique_users = len(df["person_id"].unique()) if "person_id" in df.columns else 0
        unique_doors = len(df["door_id"].unique()) if "door_id" in df.columns else 0
        return {
            "total_events": total_events,
            "unique_users": unique_users,
            "unique_doors": unique_doors,
        }
