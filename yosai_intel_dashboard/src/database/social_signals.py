from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import List


@dataclass
class SocialSignal:
    source: str
    text: str
    location: str
    sentiment: str
    threat: bool


_alerts: List[SocialSignal] = []
_lock = Lock()


def save_alert(alert: SocialSignal) -> None:
    """Persist ``alert`` to the in-memory store."""
    with _lock:
        _alerts.append(alert)


def list_alerts() -> List[SocialSignal]:
    """Return a copy of all stored alerts."""
    with _lock:
        return list(_alerts)


def clear_alerts() -> None:
    """Remove all stored alerts. Useful for tests."""
    with _lock:
        _alerts.clear()
