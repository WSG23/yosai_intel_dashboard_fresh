"""Analytics generation directly from a database connection."""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

from yosai_intel_dashboard.src.core.cache_manager import (
    CacheConfig,
    InMemoryCacheManager,
    cache_with_lock,
)
from yosai_intel_dashboard.src.database.secure_exec import execute_query
from yosai_intel_dashboard.src.utils.text_utils import safe_text

_cache_manager = InMemoryCacheManager(CacheConfig())

logger = logging.getLogger(__name__)


class DatabaseAnalyticsService:
    """Generate analytics from a database connection."""

    def __init__(self, database_manager: Any):
        self.database_manager = database_manager

    def _execute_queries(
        self, connection: Any, start_date: datetime, end_date: datetime
    ) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Run database queries and return DataFrames."""
        summary_query = """
            SELECT event_type, status, COUNT(*) as count
            FROM access_events
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY event_type, status
        """
        df_summary = pd.DataFrame(
            execute_query(connection, summary_query, (start_date, end_date))
        )

        hourly_query = """
            SELECT strftime('%H', timestamp) as hour, COUNT(*) as event_count
            FROM access_events
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY strftime('%H', timestamp)
            ORDER BY hour
        """
        df_hourly = pd.DataFrame(
            execute_query(connection, hourly_query, (start_date, end_date))
        )

        location_query = """
            SELECT location, COUNT(*) as total_events,
                   SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as successful_events
            FROM access_events
            WHERE timestamp >= ? AND timestamp <= ?
            GROUP BY location
            ORDER BY total_events DESC
        """
        df_loc = pd.DataFrame(
            execute_query(connection, location_query, (start_date, end_date))
        )

        return df_summary, df_hourly, df_loc

    def _aggregate_results(
        self, df_summary: pd.DataFrame, df_hourly: pd.DataFrame, df_loc: pd.DataFrame
    ) -> Dict[str, Any]:
        """Aggregate raw DataFrame results into the analytics structure."""
        if df_summary.empty:
            total_events = 0
            success_rate = 0.0
            breakdown = []
        else:
            total_events = int(df_summary["count"].sum())
            success_events = df_summary[df_summary["status"] == "success"][
                "count"
            ].sum()
            success_rate = (
                round((success_events / total_events) * 100, 2) if total_events else 0
            )
            breakdown = df_summary.to_dict("records")

        hourly_data = df_hourly.to_dict("records") if not df_hourly.empty else []
        peak_hour = (
            int(df_hourly.loc[df_hourly["event_count"].idxmax(), "hour"])
            if not df_hourly.empty
            else None
        )

        if df_loc.empty:
            locations = []
            busiest_location = None
        else:
            df_loc["success_rate"] = (
                df_loc["successful_events"] / df_loc["total_events"] * 100
            ).round(2)
            locations = df_loc.to_dict("records")
            busiest_location = df_loc.iloc[0]["location"] if len(df_loc) > 0 else None

        return {
            "status": "success",
            "summary": {
                "total_events": total_events,
                "success_rate": success_rate,
                "event_breakdown": breakdown,
                "period_days": 7,
            },
            "hourly_patterns": {
                "hourly_data": hourly_data,
                "peak_hour": peak_hour,
                "total_hours_analyzed": len(hourly_data),
            },
            "location_stats": {
                "locations": locations,
                "busiest_location": busiest_location,
                "total_locations": len(locations),
            },
        }

    @cache_with_lock(_cache_manager, ttl=600)
    def get_analytics(self) -> Dict[str, Any]:
        if not self.database_manager:
            return {
                "status": "error",
                "message": "Database not available",
                "error_code": "DB_NOT_AVAILABLE",
            }
        try:
            connection = self.database_manager.get_connection()
            try:
                end_date = datetime.now()
                start_date = end_date - timedelta(days=7)

                df_summary, df_hourly, df_loc = self._execute_queries(
                    connection, start_date, end_date
                )
                result = self._aggregate_results(df_summary, df_hourly, df_loc)
                result["generated_at"] = datetime.now().isoformat()
                return result
            finally:
                self.database_manager.release_connection(connection)
        except Exception as e:  # pragma: no cover - best effort
            logger.error("Database analytics error: %s", safe_text(e))
            return {
                "status": "error",
                "message": safe_text(e),
                "error_code": "DB_ANALYTICS_ERROR",
            }


__all__ = ["DatabaseAnalyticsService"]
