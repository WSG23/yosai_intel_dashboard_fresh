from __future__ import annotations

__all__ = ["_door_to_area"]


def _door_to_area(door_id: str) -> str:
    """Extract building area prefix from a door identifier."""
    return str(door_id).split("-")[0]
