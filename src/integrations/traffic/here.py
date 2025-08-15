from __future__ import annotations

from typing import Dict, List

from yosai_intel_dashboard.src.database import transport_events


def parse_here_traffic(payload: Dict) -> List[transport_events.TrafficEvent]:
    """Parse HERE traffic API payload and persist events."""
    events: List[transport_events.TrafficEvent] = []
    for item in payload.get("incidents", []):
        event = transport_events.TrafficEvent(
            event_type="incident",
            location=item["location"],
            delay_minutes=item.get("delay_minutes", 0),
            source="here",
        )
        transport_events.add_event(event)
        events.append(event)
    for item in payload.get("congestion", []):
        event = transport_events.TrafficEvent(
            event_type="congestion",
            location=item["location"],
            delay_minutes=item.get("delay_minutes", 0),
            source="here",
        )
        transport_events.add_event(event)
        events.append(event)
    return events
