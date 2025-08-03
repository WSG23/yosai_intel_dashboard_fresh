from __future__ import annotations

from typing import Dict, List

from database import transport_events


def parse_google_traffic(payload: Dict) -> List[transport_events.TrafficEvent]:
    """Parse Google traffic API payload and persist events.

    Args:
        payload: Parsed JSON from Google traffic API.

    Returns:
        List of ``TrafficEvent`` objects stored in the database.
    """
    events: List[transport_events.TrafficEvent] = []
    for item in payload.get("congestion", []):
        event = transport_events.TrafficEvent(
            event_type="congestion",
            location=item["location"],
            delay_minutes=item.get("delay_minutes", 0),
            source="google",
        )
        transport_events.add_event(event)
        events.append(event)
    for item in payload.get("incidents", []):
        event = transport_events.TrafficEvent(
            event_type="incident",
            location=item["location"],
            delay_minutes=item.get("delay_minutes", 0),
            source="google",
        )
        transport_events.add_event(event)
        events.append(event)
    return events
