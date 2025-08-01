#!/usr/bin/env python3
"""
Simplified Models Package
"""

from yosai_intel_dashboard.src.core.container import container

from .entities import Door, Facility, Person

# Import core models only
from .enums import (
    AccessResult,
    AccessType,
    AnomalyType,
    BadgeStatus,
    DoorType,
    SeverityLevel,
    TicketStatus,
)
from .events import AccessEvent, AnomalyDetection, IncidentTicket

# Flag indicating if the core models are available. This is updated when
# ``BaseModel`` is first resolved via ``__getattr__``.
BASE_MODELS_AVAILABLE = False


def __getattr__(name: str):
    """Dynamically resolve optional model services.

    The services for ``BaseModel``, ``AccessEventModel``, ``AnomalyDetectionModel``
    and ``ModelFactory`` are optional and retrieved from the dependency injection
    container when first accessed. The resolved value is cached in ``globals`` to
    avoid repeated lookups.
    """
    if name in {
        "BaseModel",
        "AccessEventModel",
        "AnomalyDetectionModel",
        "ModelFactory",
    }:
        if container.has(name):
            service = container.get(name)
        else:
            service = None
        globals()[name] = service
        if name == "BaseModel":
            globals()["BASE_MODELS_AVAILABLE"] = service is not None
        return service
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = [
    "AnomalyType",
    "AccessResult",
    "BadgeStatus",
    "SeverityLevel",
    "TicketStatus",
    "DoorType",
    "AccessType",
    "Person",
    "Door",
    "Facility",
    "AccessEvent",
    "AnomalyDetection",
    "IncidentTicket",
    "BaseModel",
    "AccessEventModel",
    "AnomalyDetectionModel",
    "ModelFactory",
    "BASE_MODELS_AVAILABLE",
]
