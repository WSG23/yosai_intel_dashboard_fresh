from __future__ import annotations

from datetime import date

from database.events import list_events
from integrations.events import ingest_all
from yosai_intel_dashboard.src.models.visitor_patterns import generate_attendance_report


def test_event_ingestion_and_correlation():
    ingest_all()
    events = list_events()
    categories = {e.category for e in events}
    assert {"meetings", "holidays", "sports", "VIP"}.issubset(categories)

    actual = {date(2024, 1, 15): 180, date(2024, 7, 4): 10}
    report = generate_attendance_report(actual)
    assert report[date(2024, 1, 15)] == {"expected": 180, "actual": 180}
    assert report[date(2024, 7, 4)] == {"expected": 20, "actual": 10}
