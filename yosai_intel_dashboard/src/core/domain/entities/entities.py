# models/entities.py
"""
Core entity models for the Yōsai Intel system
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Generic, Tuple, TypeVar, Union

T = TypeVar("T")
E = TypeVar("E")


@dataclass(frozen=True)
class Success(Generic[T]):
    value: T

    def is_success(self) -> bool:
        return True

    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True)
class Failure(Generic[E]):
    error: E

    def is_success(self) -> bool:
        return False

    def is_failure(self) -> bool:
        return True


Result = Union[Success[T], Failure[E]]


def success(value: T) -> Success[T]:
    return Success(value)


def failure(error: E) -> Failure[E]:
    return Failure(error)


from ..value_objects.enums import DoorType
from .events import AccessEvent


@dataclass(frozen=True, slots=True)
class Person:
    """Immutable Person entity with validation"""

    person_id: str
    name: str | None = None
    employee_id: str | None = None
    department: str | None = None
    clearance_level: int = 1
    access_groups: Tuple[str, ...] = field(default_factory=tuple)
    is_visitor: bool = False
    host_person_id: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    last_active: datetime | None = None
    risk_score: float = 0.0

    def __post_init__(self) -> None:
        result = self.validate()
        if result.is_failure():
            raise ValueError(f"Invalid Person: {result.error}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "person_id": self.person_id,
            "name": self.name,
            "employee_id": self.employee_id,
            "department": self.department,
            "clearance_level": self.clearance_level,
            "access_groups": self.access_groups,
            "is_visitor": self.is_visitor,
            "host_person_id": self.host_person_id,
            "created_at": self.created_at,
            "last_active": self.last_active,
            "risk_score": self.risk_score,
        }

    def validate(self) -> Result[bool, str]:
        if not self.person_id or len(self.person_id.strip()) == 0:
            return failure("person_id cannot be empty")
        if self.clearance_level < 1 or self.clearance_level > 10:
            return failure("clearance_level must be between 1 and 10")
        if self.risk_score < 0.0 or self.risk_score > 1.0:
            return failure("risk_score must be between 0.0 and 1.0")
        if self.is_visitor and not self.host_person_id:
            return failure("visitors must have a host_person_id")
        return success(True)

    def with_updated_risk_score(self, new_score: float) -> "Person":
        return Person(
            person_id=self.person_id,
            name=self.name,
            employee_id=self.employee_id,
            department=self.department,
            clearance_level=self.clearance_level,
            access_groups=self.access_groups,
            is_visitor=self.is_visitor,
            host_person_id=self.host_person_id,
            created_at=self.created_at,
            last_active=self.last_active,
            risk_score=new_score,
        )


@dataclass(slots=True)
class Door:
    """Door/Access Point entity model"""

    door_id: str
    door_name: str
    facility_id: str
    area_id: str
    floor: str | None = None
    door_type: DoorType = DoorType.STANDARD
    required_clearance: int = 1
    is_critical: bool = False
    location_coordinates: Tuple[float, float] | None = None
    device_id: str | None = None
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "door_id": self.door_id,
            "door_name": self.door_name,
            "facility_id": self.facility_id,
            "area_id": self.area_id,
            "floor": self.floor,
            "door_type": self.door_type.value,
            "required_clearance": self.required_clearance,
            "is_critical": self.is_critical,
            "location_coordinates": self.location_coordinates,
            "device_id": self.device_id,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


@dataclass(slots=True)
class Facility:
    """Facility entity model"""

    facility_id: str
    facility_name: str
    campus_id: str | None = None
    address: str | None = None
    timezone: str = "UTC"
    operating_hours: Dict[str, Any] = field(default_factory=dict)
    security_level: int = 1
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "facility_id": self.facility_id,
            "facility_name": self.facility_name,
            "campus_id": self.campus_id,
            "address": self.address,
            "timezone": self.timezone,
            "operating_hours": self.operating_hours,
            "security_level": self.security_level,
            "is_active": self.is_active,
            "created_at": self.created_at,
        }


# Re-export AccessEvent for backwards compatibility
__all__ = [
    "Person",
    "Door",
    "Facility",
    "AccessEvent",
]
