from __future__ import annotations

from typing import Dict, List

from yosai_intel_dashboard.src.database import transport_events


def parse_transit_feed(payload: Dict) -> List[transport_events.TrafficEvent]:
    """Parse public transit feed and persist schedule events."""
    events: List[transport_events.TrafficEvent] = []
    for item in payload.get("schedules", []):
        event = transport_events.TrafficEvent(
            event_type="schedule",
            location=item["stop"],
            delay_minutes=item.get("delay_minutes", 0),
            source="transit",
        )
        transport_events.add_event(event)
        events.append(event)
    return events
