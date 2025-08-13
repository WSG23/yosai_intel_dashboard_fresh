from __future__ import annotations

from datetime import datetime, timedelta
from importlib import import_module

from services.arrival_estimator import ArrivalEstimator

transport_events = import_module("yosai_intel_dashboard.src.database.transport_events")


def test_estimate_uses_transport_delays() -> None:
    transport_events.clear_events()
    transport_events.add_event(
        transport_events.TrafficEvent(
            event_type="incident", location="Main", delay_minutes=5, source="t"
        )
    )
    estimator = ArrivalEstimator(base_speed_kmph=60)
    start = datetime(2024, 1, 1, 8, 0, 0)
    arrival = estimator.estimate(distance_km=30, location="Main", start_time=start)
    assert arrival == start + timedelta(minutes=35)


def test_estimate_defaults_start_time() -> None:
    transport_events.clear_events()
    estimator = ArrivalEstimator(base_speed_kmph=60)
    before = datetime.utcnow()
    arrival = estimator.estimate(distance_km=60, location="None")
    after = datetime.utcnow()
    assert timedelta(minutes=59) <= arrival - after <= timedelta(minutes=61)
    assert arrival >= before
