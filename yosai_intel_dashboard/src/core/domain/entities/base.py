#!/usr/bin/env python3
"""Base classes for data models used throughout the application."""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BaseModel:
    """Base class for all models"""

    data_source: Any | None = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "created_at": self.created_at.isoformat(),
            "data_source": str(self.data_source) if self.data_source else None,
        }

    def validate(self) -> bool:
        """Validate model data"""
        return True


@dataclass(slots=True)
class AccessEventModel(BaseModel):
    """Model for access control events"""

    events: List[Dict[str, Any]] = field(default_factory=list)

    def load_from_dataframe(self, df: pd.DataFrame) -> bool:
        """Load events from pandas DataFrame"""
        try:
            if df is None or df.empty:
                logger.warning("Empty DataFrame provided to AccessEventModel")
                return False

            self.events = df.to_dict("records")
            logger.info(f"Loaded {len(self.events)} access events")
            return True

        except Exception as e:
            logger.error(f"Error loading DataFrame into AccessEventModel: {e}")
            return False

    def get_user_activity(self) -> Dict[str, int]:
        """Get user activity summary"""
        if not self.events:
            return {}

        try:
            user_counts = {}
            for event in self.events:
                user_id = event.get("user_id") or event.get("person_id") or "unknown"
                user_counts[user_id] = user_counts.get(user_id, 0) + 1
            return user_counts
        except Exception as e:
            logger.error(f"Error calculating user activity: {e}")
            return {}

    def get_door_activity(self) -> Dict[str, int]:
        """Get door activity summary"""
        if not self.events:
            return {}

        try:
            door_counts = {}
            for event in self.events:
                door_id = event.get("door_id") or event.get("location") or "unknown"
                door_counts[door_id] = door_counts.get(door_id, 0) + 1
            return door_counts
        except Exception as e:
            logger.error(f"Error calculating door activity: {e}")
            return {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with analytics"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "total_events": len(self.events),
                "user_activity": self.get_user_activity(),
                "door_activity": self.get_door_activity(),
                "access_patterns": self._get_access_patterns(),
            }
        )
        return base_dict

    def _get_access_patterns(self) -> Dict[str, Any]:
        """Analyze access patterns"""
        if not self.events:
            return {}

        try:
            patterns = {
                "total_access_attempts": len(self.events),
                "successful_attempts": 0,
                "failed_attempts": 0,
                "hourly_distribution": {},
            }

            for event in self.events:
                # Count success/failure
                result = str(event.get("access_result", "")).lower()
                if "grant" in result or "success" in result:
                    patterns["successful_attempts"] += 1
                elif "den" in result or "fail" in result:
                    patterns["failed_attempts"] += 1

                # Hour distribution
                timestamp = event.get("timestamp", "")
                if timestamp:
                    try:
                        if isinstance(timestamp, str):
                            hour = pd.to_datetime(timestamp).hour
                        else:
                            hour = timestamp.hour
                        patterns["hourly_distribution"][hour] = (
                            patterns["hourly_distribution"].get(hour, 0) + 1
                        )
                    except Exception:
                        pass

            return patterns
        except Exception as e:
            logger.error(f"Error analyzing access patterns: {e}")
            return {}


@dataclass(slots=True)
class AnomalyDetectionModel(BaseModel):
    """Model for anomaly detection"""

    anomalies: List[Dict[str, Any]] = field(default_factory=list)

    def detect_anomalies(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Detect anomalies in access events"""
        if not events:
            return []

        try:
            anomalies = []

            for event in events:
                # After hours access (simple check)
                timestamp = str(event.get("timestamp", ""))
                if any(
                    hour in timestamp
                    for hour in ["22:", "23:", "00:", "01:", "02:", "03:", "04:", "05:"]
                ):
                    anomalies.append(
                        {
                            "type": "after_hours_access",
                            "event": event,
                            "description": "Access attempt after business hours",
                            "severity": "medium",
                        }
                    )

                # Failed access attempts
                result = str(event.get("access_result", "")).lower()
                if any(
                    fail_word in result
                    for fail_word in ["denied", "failed", "fail", "reject"]
                ):
                    anomalies.append(
                        {
                            "type": "failed_access",
                            "event": event,
                            "description": "Failed access attempt",
                            "severity": "high",
                        }
                    )

            self.anomalies = anomalies
            return anomalies

        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        base_dict = super().to_dict()
        base_dict.update(
            {
                "total_anomalies": len(self.anomalies),
                "anomaly_types": self._count_anomaly_types(),
                "severity_distribution": self._count_severity(),
            }
        )
        return base_dict

    def _count_anomaly_types(self) -> Dict[str, int]:
        """Count anomalies by type"""
        counts = {}
        for anomaly in self.anomalies:
            anomaly_type = anomaly.get("type", "unknown")
            counts[anomaly_type] = counts.get(anomaly_type, 0) + 1
        return counts

    def _count_severity(self) -> Dict[str, int]:
        """Count anomalies by severity"""
        counts = {}
        for anomaly in self.anomalies:
            severity = anomaly.get("severity", "unknown")
            counts[severity] = counts.get(severity, 0) + 1
        return counts


class ModelFactory:
    """Factory for creating model instances"""

    @staticmethod
    def create_access_model(data_source: Any | None = None) -> AccessEventModel:
        """Create AccessEventModel instance"""
        return AccessEventModel(data_source)

    @staticmethod
    def create_anomaly_model(
        data_source: Any | None = None,
    ) -> AnomalyDetectionModel:
        """Create AnomalyDetectionModel instance"""
        return AnomalyDetectionModel(data_source)

    @staticmethod
    def create_models_from_dataframe(df: pd.DataFrame) -> Dict[str, BaseModel]:
        """Create all models from a DataFrame"""
        models = {}

        try:
            if df is None or df.empty:
                logger.warning("Empty DataFrame provided to ModelFactory")
                return {}
            # Create access model
            access_model = ModelFactory.create_access_model(df)
            if access_model.load_from_dataframe(df):
                models["access"] = access_model

            # Create anomaly model
            anomaly_model = ModelFactory.create_anomaly_model(df)
            events = df.to_dict("records") if not df.empty else []
            anomaly_model.detect_anomalies(events)
            models["anomaly"] = anomaly_model

            logger.info(f"Created {len(models)} models from DataFrame")
            return models

        except Exception as e:
            logger.error(f"Error creating models from DataFrame: {e}")
            return {}

    @staticmethod
    def create_all_models(df: pd.DataFrame) -> Dict[str, BaseModel]:
        """Alias for ``create_models_from_dataframe`` for backward compatibility."""
        return ModelFactory.create_models_from_dataframe(df)

    @staticmethod
    def get_analytics_from_models(models: Dict[str, BaseModel]) -> Dict[str, Any]:
        """Extract analytics from all models"""
        analytics = {}

        try:
            if "access" in models:
                access_data = models["access"].to_dict()
                analytics.update(
                    {
                        "total_events": access_data.get("total_events", 0),
                        "top_users": [
                            {"user_id": k, "count": v}
                            for k, v in sorted(
                                access_data.get("user_activity", {}).items(),
                                key=lambda x: x[1],
                                reverse=True,
                            )[:10]
                        ],
                        "top_doors": [
                            {"door_id": k, "count": v}
                            for k, v in sorted(
                                access_data.get("door_activity", {}).items(),
                                key=lambda x: x[1],
                                reverse=True,
                            )[:10]
                        ],
                        "access_patterns": access_data.get("access_patterns", {}),
                    }
                )

            if "anomaly" in models:
                anomaly_data = models["anomaly"].to_dict()
                analytics["anomalies"] = {
                    "total_anomalies": anomaly_data.get("total_anomalies", 0),
                    "anomaly_types": anomaly_data.get("anomaly_types", {}),
                    "severity_distribution": anomaly_data.get(
                        "severity_distribution", {}
                    ),
                }

            return analytics

        except Exception as e:
            logger.error(f"Error extracting analytics from package models: {e}")
            return {}


__all__ = ["BaseModel", "AccessEventModel", "AnomalyDetectionModel", "ModelFactory"]
