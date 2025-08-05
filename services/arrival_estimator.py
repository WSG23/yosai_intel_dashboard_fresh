from __future__ import annotations

from datetime import datetime, timedelta

from yosai_intel_dashboard.src.database import transport_events


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
        delay_minutes = transport_events.total_delay(location)
        return start_time + timedelta(minutes=travel_minutes + delay_minutes)
