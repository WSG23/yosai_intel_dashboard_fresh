from __future__ import annotations

from datetime import datetime, timedelta

from integrations.traffic import (
    parse_google_traffic,
    parse_here_traffic,
    parse_transit_feed,
)
from services.arrival_estimator import ArrivalEstimator
from yosai_intel_dashboard.src.database import transport_events


def test_feed_parsing() -> None:
    transport_events.clear_events()
    google_data = {
        "congestion": [{"location": "Main St", "delay_minutes": 5}],
        "incidents": [{"location": "Main St", "delay_minutes": 3}],
    }
    here_data = {
        "incidents": [{"location": "Main St", "delay_minutes": 2}],
    }
    transit_data = {
        "schedules": [{"stop": "Main St", "delay_minutes": 1}],
    }

    parse_google_traffic(google_data)
    parse_here_traffic(here_data)
    parse_transit_feed(transit_data)

    events = list(transport_events.get_events())
    assert len(events) == 4
    assert transport_events.total_delay("Main St") == 11


def test_prediction_accuracy() -> None:
    transport_events.clear_events()
    parse_google_traffic({"congestion": [{"location": "Route", "delay_minutes": 4}]})

    estimator = ArrivalEstimator(base_speed_kmph=60)
    start = datetime(2024, 1, 1, 8, 0, 0)
    arrival = estimator.estimate(distance_km=30, location="Route", start_time=start)

    assert arrival == start + timedelta(minutes=34)
