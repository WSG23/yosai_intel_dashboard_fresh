"""Visitor pattern models incorporating event schedules."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Dict

from yosai_intel_dashboard.src.database.events import list_events

CATEGORY_EXPECTED = {
    "meetings": 50,
    "holidays": 20,
    "sports": 100,
    "VIP": 30,
}


def generate_attendance_report(actual: Dict[date, int]) -> Dict[date, Dict[str, int]]:
    """Generate expected vs actual attendance keyed by date."""
    expected_totals: Dict[date, int] = defaultdict(int)
    for event in list_events():
        expected_totals[event.start.date()] += CATEGORY_EXPECTED.get(event.category, 0)

    report: Dict[date, Dict[str, int]] = {}
    for day, expected in expected_totals.items():
        report[day] = {"expected": expected, "actual": actual.get(day, 0)}
    return report
