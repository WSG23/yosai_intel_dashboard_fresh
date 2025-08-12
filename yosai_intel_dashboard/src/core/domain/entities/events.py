# models/events.py
"""
Event and transaction models for the Yōsai Intel system
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict

from ..value_objects.enums import (
    AccessResult,
    AnomalyType,
    BadgeStatus,
    SeverityLevel,
    TicketStatus,
)


@dataclass(slots=True)
class AccessEvent:
    """Core access control event model"""

    event_id: str
    timestamp: datetime
    person_id: str
    door_id: str
    badge_id: str | None = None
    access_result: AccessResult = AccessResult.DENIED
    badge_status: BadgeStatus = BadgeStatus.INVALID
    door_held_open_time: float = 0.0
    entry_without_badge: bool = False
    device_status: str = "normal"
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp,
            "person_id": self.person_id,
            "door_id": self.door_id,
            "badge_id": self.badge_id,
            "access_result": self.access_result.value,
            "badge_status": self.badge_status.value,
            "door_held_open_time": self.door_held_open_time,
            "entry_without_badge": self.entry_without_badge,
            "device_status": self.device_status,
            "raw_data": self.raw_data,
        }


@dataclass(slots=True)
class AnomalyDetection:
    """Anomaly detection result model"""

    anomaly_id: str
    event_id: str
    anomaly_type: AnomalyType
    severity: SeverityLevel
    confidence_score: float
    description: str
    detected_at: datetime
    ai_model_version: str | None = None
    additional_context: Dict[str, Any] = field(default_factory=dict)
    is_verified: bool | None = None
    verified_by: str | None = None
    verified_at: datetime | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "anomaly_id": self.anomaly_id,
            "event_id": self.event_id,
            "anomaly_type": self.anomaly_type.value,
            "severity": self.severity.value,
            "confidence_score": self.confidence_score,
            "description": self.description,
            "detected_at": self.detected_at,
            "ai_model_version": self.ai_model_version,
            "additional_context": self.additional_context,
            "is_verified": self.is_verified,
            "verified_by": self.verified_by,
            "verified_at": self.verified_at,
        }


@dataclass(slots=True)
class IncidentTicket:
    """Security incident ticket model"""

    ticket_id: str
    event_id: str
    anomaly_id: str | None = None
    status: TicketStatus = TicketStatus.NEW
    threat_score: int = 0  # 0-100
    facility_location: str = ""
    area: str = ""
    device_id: str | None = None
    access_group: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    assigned_to: str | None = None
    resolved_at: datetime | None = None
    resolution_type: str | None = None
    resolution_notes: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "ticket_id": self.ticket_id,
            "event_id": self.event_id,
            "anomaly_id": self.anomaly_id,
            "status": self.status.value,
            "threat_score": self.threat_score,
            "facility_location": self.facility_location,
            "area": self.area,
            "device_id": self.device_id,
            "access_group": self.access_group,
            "created_at": self.created_at,
            "assigned_to": self.assigned_to,
            "resolved_at": self.resolved_at,
            "resolution_type": self.resolution_type,
            "resolution_notes": self.resolution_notes,
        }
