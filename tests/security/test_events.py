import pytest

from security import events
from security.events import SecurityEvent


def test_threat_detected_dispatch(monkeypatch):
    called = {}

    def fake(event, data=None):
        called["event"] = event
        called["data"] = data

    monkeypatch.setattr(events.security_unified_callbacks, "trigger_event", fake)

    events.emit_security_event(SecurityEvent.THREAT_DETECTED, {"x": 1})

    assert called == {"event": SecurityEvent.THREAT_DETECTED, "data": {"x": 1}}
