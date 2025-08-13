"""Simple arrival time estimation utilities used in tests."""

from __future__ import annotations

from datetime import datetime, timedelta
from importlib import import_module
from typing import TYPE_CHECKING, Protocol, cast


class _TransportEvents(Protocol):
    """Protocol for the transport events module used at runtime."""

    def total_delay(self, location: str) -> float: ...
    def clear_events(self) -> None: ...
    def add_event(self, event: object) -> None: ...


# Dynamically import the real implementation to avoid pulling in the entire
# application during type checking.  ``mypy`` treats the result as ``Any`` so we
# cast it to our protocol for type safety.
if TYPE_CHECKING:
    _transport_events = cast(_TransportEvents, object())
else:  # pragma: no cover - runtime import only
    _transport_events = cast(
        _TransportEvents,
        import_module("yosai_intel_dashboard.src.database.transport_events"),
    )


class ArrivalEstimator:
    """Estimate arrival times using transport event data."""

    def __init__(self, base_speed_kmph: float = 40.0) -> None:
        self.base_speed = base_speed_kmph

    def estimate(
        self,
        distance_km: float,
        location: str,
        start_time: datetime | None = None,
    ) -> datetime:
        """Estimate arrival time for a trip.

        Args:
            distance_km: Distance to travel.
            location: Location identifier used to look up transport events.
            start_time: Starting time of the trip. Defaults to ``datetime.utcnow``.
        """
        if start_time is None:
            start_time = datetime.utcnow()
        travel_minutes = (distance_km / self.base_speed) * 60
        delay_minutes = _transport_events.total_delay(location)
        return start_time + timedelta(minutes=travel_minutes + delay_minutes)
