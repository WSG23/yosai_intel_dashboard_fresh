# models/enums.py
"""
Enums and constants for the Yōsai Intel system
"""

from enum import Enum


class AnomalyType(Enum):
    """Types of anomalies that can be detected"""

    NO_ACCESS = "no-access-anomaly"
    CRITICAL_DOOR = "critical-door-anomaly"
    PROBABLE_TAILGATE = "probable-tailgate-anomaly"
    ODD_DOOR = "odd-door-anomaly"
    ODD_TIME = "odd-time-anomaly"
    ODD_PATH = "odd-path-anomaly"
    ODD_AREA = "odd-area-anomaly"
    ODD_AREA_TIME = "unusual-time-area-combo"
    MULTIPLE_ATTEMPTS = "multiple-attempts-anomaly"
    BADGE_CLONE_SUSPECTED = "badge-clone-suspected"
    FORCED_ENTRY = "forced-entry-or-door-held-open"
    ACCESS_NO_EXIT = "access-granted-no-exit-anomaly"
    PATTERN_DRIFT = "access-pattern-drift-anomaly"
    ACCESS_OUTSIDE_CLEARANCE = "access-outside-clearance-anomaly"
    UNACCOMPANIED_VISITOR = "unaccompanied-visitor-anomaly"
    COMPOSITE_SCORE = "composite-anomaly-score"


class AccessResult(Enum):
    """Access control results"""

    GRANTED = "Granted"
    DENIED = "Denied"
    TIMEOUT = "Timeout"
    ERROR = "Error"


class BadgeStatus(Enum):
    """Badge status values"""

    VALID = "Valid"
    INVALID = "Invalid"
    EXPIRED = "Expired"
    SUSPENDED = "Suspended"


class SeverityLevel(Enum):
    """Severity levels for incidents and anomalies"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TicketStatus(Enum):
    """Incident ticket status values"""

    NEW = "ticket-new"
    OPEN = "ticket-open"
    LOCKED = "ticket-locked"
    RESOLVED_HARMFUL = "ticket-harmful"
    RESOLVED_MALFUNCTION = "resolved-malfunction"
    RESOLVED_NORMAL = "resolved-normal"
    DISMISSED = "dismissed"


class DoorType(Enum):
    """Types of doors/access points"""

    STANDARD = "standard"
    CRITICAL = "critical"
    RESTRICTED = "restricted"
    EMERGENCY = "emergency"
    VISITOR = "visitor"


class AccessType(Enum):
    """Access categories for facilities"""

    PUBLIC = "public"
    PRIVATE = "private"
    EMPLOYEE = "employee"
    VISITOR = "visitor"
    RESTRICTED = "restricted"
