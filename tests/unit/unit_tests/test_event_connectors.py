from __future__ import annotations

from integrations.events import internal_calendar, public_api, transportation
from yosai_intel_dashboard.src.database import events as event_store


def test_event_connectors_and_store():
    event_store.clear_events()
    all_events = []
    all_events += internal_calendar.fetch_events()
    all_events += public_api.fetch_events()
    all_events += transportation.fetch_events()
    event_store.add_events(all_events)
    stored = event_store.list_events()
    assert stored == all_events
    names = [e.name for e in stored]
    assert names == [
        "Board Meeting",
        "City Marathon",
        "Independence Day",
        "VIP Arrival",
    ]
