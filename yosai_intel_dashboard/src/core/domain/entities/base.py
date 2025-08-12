#!/usr/bin/env python3
from __future__ import annotations

"""Base classes for data models used throughout the application."""
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Iterable, List, Protocol, runtime_checkable

import pandas as pd

from ..value_objects.enums import AccessResult
from .events import AccessEvent

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


@runtime_checkable
class AccessEventCollection(Protocol):
    """Iterable collection of :class:`AccessEvent` instances."""

    def __iter__(self) -> Iterable[AccessEvent]:
        ...


@dataclass(slots=True)
class AccessEventModel(BaseModel):
    """Model for access control events"""

    events: List[AccessEvent] = field(default_factory=list)

    def load(self, events: AccessEventCollection) -> bool:
        """Load access events from an iterable collection."""
        try:
            event_list = list(events)
            if not event_list:
                logger.warning("Empty events provided to AccessEventModel")
                return False
            self.events = event_list
            logger.info(f"Loaded {len(self.events)} access events")
            return True
        except Exception as exc:  # pragma: no cover - defensive
            logger.error(f"Error loading events into AccessEventModel: {exc}")
            return False

    def get_user_activity(self) -> Dict[str, int]:
        """Get user activity summary"""
        if not self.events:
            return {}
        counts: Dict[str, int] = {}
        for event in self.events:
            user_id = getattr(event, "person_id", None) or getattr(event, "user_id", None)
            if user_id:
                counts[user_id] = counts.get(user_id, 0) + 1
        return counts

    def get_door_activity(self) -> Dict[str, int]:
        """Get door activity summary"""
        if not self.events:
            return {}
        counts: Dict[str, int] = {}
        for event in self.events:
            door_id = getattr(event, "door_id", None) or getattr(event, "location", None)
            if door_id:
                counts[door_id] = counts.get(door_id, 0) + 1
        return counts

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

        patterns: Dict[str, Any] = {
            "total_access_attempts": len(self.events),
            "successful_attempts": 0,
            "failed_attempts": 0,
            "hourly_distribution": {},
        }

        for event in self.events:
            result = getattr(event, "access_result", None)
            result_val = result.value if isinstance(result, AccessResult) else str(result)
            result_val = str(result_val).lower()
            if "grant" in result_val or "success" in result_val:
                patterns["successful_attempts"] += 1
            elif "den" in result_val or "fail" in result_val:
                patterns["failed_attempts"] += 1

            ts = getattr(event, "timestamp", None)
            if isinstance(ts, datetime):
                hour = ts.hour
                hourly = patterns["hourly_distribution"]
                hourly[hour] = hourly.get(hour, 0) + 1

        return patterns


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
            from ....adapters.access_event_dataframe import dataframe_to_events

            events = dataframe_to_events(df)
            if not events:
                logger.warning("Empty DataFrame provided to ModelFactory")
                return {}

            # Create access model
            access_model = ModelFactory.create_access_model()
            if access_model.load(events):
                models["access"] = access_model

            # Create anomaly model
            anomaly_model = ModelFactory.create_anomaly_model()
            anomaly_model.detect_anomalies([e.to_dict() for e in events])
            models["anomaly"] = anomaly_model

            logger.info(f"Created {len(models)} models from DataFrame")
            return models

        except Exception as e:  # pragma: no cover - defensive
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


__all__ = [
    "BaseModel",
    "AccessEventCollection",
    "AccessEventModel",
    "AnomalyDetectionModel",
    "ModelFactory",
]
