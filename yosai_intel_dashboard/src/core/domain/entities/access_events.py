# models/access_events.py - Type-safe, modular access events model
"""
Access Events Data Model for Yōsai Intel Dashboard
Handles all database operations for access control events
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
from typing import Any, Dict

import pandas as pd

from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.query_optimizer import monitor_query_performance
from yosai_intel_dashboard.src.database.secure_exec import (
    execute_command,
    execute_query,
)
from yosai_intel_dashboard.src.infrastructure.config.constants import (
    DataProcessingLimits,
)

from .base import BaseModel
from .enums import AccessResult, BadgeStatus

_sql_validator = SecurityValidator()


class AccessEventModel(BaseModel):
    """Model for access control events with full type safety"""

    @monitor_query_performance()
    def get_data(
        self, filters: Dict[str, Any] | None = None, user: Any | None = None
    ) -> pd.DataFrame:
        """Get access events with optional filtering"""

        parts = [
            """
        SELECT
            event_id,
            timestamp,
            person_id,
            door_id,
            badge_id,
            access_result,
            badge_status,
            door_held_open_time,
            entry_without_badge,
            device_status
        FROM access_events
        WHERE 1=1
        """,
        ]

        params = []

        # Use empty dict if filters is None
        if filters is None:
            filters = {}

        # Build dynamic query with filters
        if "start_date" in filters:
            parts.append("AND timestamp >= %s")
            params.append(filters["start_date"])

        if "end_date" in filters:
            parts.append("AND timestamp <= %s")
            params.append(filters["end_date"])

        if "person_id" in filters:
            if user is not None:
                _sql_validator.validate_resource_access(user, filters["person_id"])
            parts.append("AND person_id = %s")
            params.append(filters["person_id"])

        if "door_id" in filters:
            if user is not None:
                _sql_validator.validate_resource_access(user, filters["door_id"])
            parts.append("AND door_id = %s")
            params.append(filters["door_id"])

        if "access_result" in filters:
            parts.append("AND access_result = %s")
            params.append(filters["access_result"])
        parts.append("ORDER BY timestamp DESC LIMIT %s")
        params.append(DataProcessingLimits.DEFAULT_QUERY_LIMIT)
        query = " ".join(parts)

        try:
            df = execute_query(self.db, query, tuple(params))
            return self._process_dataframe(df) if df is not None else pd.DataFrame()
        except Exception as e:
            logging.error(f"Error fetching access events: {e}")
            return pd.DataFrame()

    def _process_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process and validate DataFrame from database"""
        if df.empty:
            return df

        try:
            # Convert timestamp to datetime
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])

            # Validate enum values
            if "access_result" in df.columns:
                valid_results = [result.value for result in AccessResult]
                df = df[df["access_result"].isin(valid_results)]

            if "badge_status" in df.columns:
                valid_statuses = [status.value for status in BadgeStatus]
                df = df[df["badge_status"].isin(valid_statuses)]

            return df
        except Exception as e:
            logging.error(f"Error processing DataFrame: {e}")
            return df

    @monitor_query_performance()
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get comprehensive summary statistics"""
        query = """
        SELECT
            COUNT(*) as total_events,
            COUNT(DISTINCT person_id) as unique_people,
            COUNT(DISTINCT door_id) as unique_doors,
            SUM(
                CASE WHEN access_result = 'Granted' THEN 1 ELSE 0 END
            ) as granted_events,
            SUM(
                CASE WHEN access_result = 'Denied' THEN 1 ELSE 0 END
            ) as denied_events
        FROM access_events
        WHERE timestamp >= date('now', '-30 days')
        """

        try:
            result = execute_query(self.db, query)
            if result is not None and not result.empty:
                stats = result.iloc[0].to_dict()

                # Calculate derived metrics
                total = stats.get("total_events", 0)
                granted = stats.get("granted_events", 0)

                if total > 0:
                    stats["granted_rate"] = (granted / total) * 100
                    stats["denied_rate"] = ((total - granted) / total) * 100
                else:
                    stats["granted_rate"] = 0
                    stats["denied_rate"] = 0

                return stats

            return {}
        except Exception as e:
            logging.error(f"Error getting summary stats: {e}")
            return {}

    @monitor_query_performance()
    def get_recent_events(self, hours: int = 24) -> pd.DataFrame:
        """Get recent events for real-time monitoring"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        return self.get_data({"start_date": cutoff_time})

    @monitor_query_performance()
    def get_hourly_distribution(self, days: int = 7) -> pd.DataFrame:
        """Get hourly access distribution for analytics"""
        _sql_validator.validate_input(str(days), "query_parameter")
        query = """
        SELECT
            strftime('%H', timestamp) as hour,
            COUNT(*) as event_count,
            SUM(CASE WHEN access_result = 'Granted' THEN 1 ELSE 0 END) as granted_count
        FROM access_events
        WHERE timestamp >= date('now', %s)
        GROUP BY strftime('%H', timestamp)
        ORDER BY hour
        """
        params = (f"-{days} days",)

        try:
            result = execute_query(self.db, query, params)
            return result if result is not None else pd.DataFrame()
        except Exception as e:
            logging.error(f"Error getting hourly distribution: {e}")
            return pd.DataFrame()

    @monitor_query_performance()
    def get_user_activity(self, limit: int = 20) -> pd.DataFrame:
        """Get top active users"""
        query = """
        SELECT
            person_id,
            COUNT(*) as total_events,
              SUM(
                  CASE WHEN access_result = 'Granted' THEN 1 ELSE 0 END
              ) as granted_events,
            MAX(timestamp) as last_access
        FROM access_events
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY person_id
        ORDER BY total_events DESC
        LIMIT %s
        """

        try:
            result = execute_query(self.db, query, (limit,))
            return result if result is not None else pd.DataFrame()
        except Exception as e:
            logging.error(f"Error getting user activity: {e}")
            return pd.DataFrame()

    @monitor_query_performance()
    def get_door_activity(self, limit: int = 20) -> pd.DataFrame:
        """Get most accessed doors"""
        query = """
        SELECT
            door_id,
            COUNT(*) as total_events,
              SUM(
                  CASE WHEN access_result = 'Granted' THEN 1 ELSE 0 END
              ) as granted_events,
            COUNT(DISTINCT person_id) as unique_users
        FROM access_events
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY door_id
        ORDER BY total_events DESC
        LIMIT %s
        """

        try:
            result = execute_query(self.db, query, (limit,))
            return result if result is not None else pd.DataFrame()
        except Exception as e:
            logging.error(f"Error getting door activity: {e}")
            return pd.DataFrame()

    @monitor_query_performance()
    def get_trend_analysis(self, days: int = 30) -> pd.DataFrame:
        """Get daily trend analysis"""
        _sql_validator.validate_input(str(days), "query_parameter")
        query = """
        SELECT
            date(timestamp) as date,
            COUNT(*) as total_events,
              SUM(
                  CASE WHEN access_result = 'Granted' THEN 1 ELSE 0 END
              ) as granted_events,
            COUNT(DISTINCT person_id) as unique_users,
            COUNT(DISTINCT door_id) as unique_doors
        FROM access_events
        WHERE timestamp >= date('now', %s)
        GROUP BY date(timestamp)
        ORDER BY date
        """
        params = (f"-{days} days",)

        try:
            result = execute_query(self.db, query, params)
            if result is not None and not result.empty:
                # Add calculated columns
                result["denied_events"] = (
                    result["total_events"] - result["granted_events"]
                )
                result["success_rate"] = (
                    result["granted_events"] / result["total_events"] * 100
                ).round(2)
                return result
            return pd.DataFrame()
        except Exception as e:
            logging.error(f"Error getting trend analysis: {e}")
            return pd.DataFrame()

    def validate_data(self, data: pd.DataFrame) -> bool:
        """Validate access events data structure"""
        if data is None or data.empty:
            return False

        required_columns = [
            "event_id",
            "timestamp",
            "person_id",
            "door_id",
            "access_result",
        ]

        # Check for required columns
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            logging.error(f"Missing required columns: {missing_columns}")
            return False

        # Validate data types
        try:
            # Check timestamp format
            pd.to_datetime(data["timestamp"].iloc[0])

            # Check access_result values
            valid_results = [result.value for result in AccessResult]
            invalid_results = data[~data["access_result"].isin(valid_results)][
                "access_result"
            ].unique()
            if len(invalid_results) > 0:
                logging.warning(f"Invalid access results found: {invalid_results}")

            return True

        except Exception as e:
            logging.error(f"Data validation failed: {e}")
            return False

    @monitor_query_performance()
    def create_event(self, event_data: Dict[str, Any]) -> bool:
        """Create a new access event"""
        required_fields = [
            "event_id",
            "timestamp",
            "person_id",
            "door_id",
            "access_result",
        ]

        # Validate required fields
        if not all(field in event_data for field in required_fields):
            logging.error("Missing required fields for event creation")
            return False

        query = """
        INSERT INTO access_events
        (event_id, timestamp, person_id, door_id, badge_id, access_result,
         badge_status, door_held_open_time, entry_without_badge, device_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """

        params = (
            event_data["event_id"],
            event_data["timestamp"],
            event_data["person_id"],
            event_data["door_id"],
            event_data.get("badge_id"),
            event_data["access_result"],
            event_data.get("badge_status", "Valid"),
            event_data.get("door_held_open_time", 0.0),
            event_data.get("entry_without_badge", False),
            event_data.get("device_status", "normal"),
        )

        try:
            execute_command(self.db, query, params)
            logging.info(f"Created access event: {event_data['event_id']}")
            return True
        except Exception as e:
            logging.error(f"Failed to create access event: {e}")
            return False


# Factory function for easy instantiation
def create_access_event_model(db_connection=None) -> AccessEventModel:
    """Factory function to create AccessEventModel instance"""
    if db_connection is None:
        from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
            get_database,
        )

        db_connection = get_database()

    return AccessEventModel(db_connection)


# Export the model class and factory
__all__ = ["AccessEventModel", "create_access_event_model"]
