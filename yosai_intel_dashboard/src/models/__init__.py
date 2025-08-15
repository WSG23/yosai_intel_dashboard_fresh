#!/usr/bin/env python3
"""
Simplified Models Package
"""

from yosai_intel_dashboard.src.core.container import container

# Core models are optional in the lightweight test environment.  Import them
# defensively so missing optional dependencies do not break simple use cases.
try:  # pragma: no cover - exercised indirectly
    from .entities import Door, Facility, Person
except Exception:  # noqa: BLE001 - best effort fallback
    Door = Facility = Person = object  # type: ignore[misc,assignment]

# Import core enums if available, otherwise provide dummy placeholders.
try:  # pragma: no cover - exercised indirectly
    from ..core.domain.value_objects.enums import (
        AccessResult,
        AccessType,
        AnomalyType,
        BadgeStatus,
        DoorType,
        SeverityLevel,
        TicketStatus,
    )
except Exception:  # noqa: BLE001 - best effort fallback
    AccessResult = AccessType = AnomalyType = BadgeStatus = DoorType = SeverityLevel = (
        TicketStatus
    ) = object  # type: ignore[misc,assignment]

# Import event models if available.
try:  # pragma: no cover - exercised indirectly
    from .events import AccessEvent, AnomalyDetection, IncidentTicket
except Exception:  # noqa: BLE001 - best effort fallback
    AccessEvent = AnomalyDetection = IncidentTicket = object  # type: ignore[misc,assignment]

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
