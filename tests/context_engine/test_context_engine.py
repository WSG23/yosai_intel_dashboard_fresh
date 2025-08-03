import datetime as dt

import pytest

from yosai_intel_dashboard.src.services.context_engine import (
    ContextEngine,
    SecurityEvent,
    EnvironmentalEvent,
)


class FakeProducer:
    """Collect messages sent by the engine for inspection."""

    def __init__(self) -> None:
        self.messages = []

    def produce(self, topic, value, *args, **kwargs):  # pragma: no cover - simple stub
        self.messages.append((topic, value))


@pytest.mark.integration
def test_windowed_join_and_publish():
    producer = FakeProducer()
    engine = ContextEngine(producer, alert_topic="alerts", window_size=30)

    now = dt.datetime.utcnow()
    security_events = [
        SecurityEvent(device_id="d1", ts=now, threat_level=7, factor="auth"),
    ]
    environmental_events = [
        EnvironmentalEvent(
            device_id="d1", ts=now + dt.timedelta(seconds=5), temperature=25.0, humidity=0.5
        ),
        # outside the window
        EnvironmentalEvent(
            device_id="d1", ts=now + dt.timedelta(seconds=50), temperature=30.0, humidity=0.4
        ),
    ]

    alerts = engine.process_events(security_events, environmental_events)

    assert len(alerts) == 1
    alert = alerts[0]
    assert alert["device_id"] == "d1"
    assert pytest.approx(alert["temperature"], 0.01) == 25.0
    # ensure message was published to Kafka producer
    assert producer.messages[0][0] == "alerts"
    assert producer.messages[0][1]["device_id"] == "d1"
    assert 0 < alert["confidence"] <= 1.0


@pytest.mark.integration
def test_conflict_resolution_uses_latest_environmental_reading():
    producer = FakeProducer()
    engine = ContextEngine(producer, alert_topic="alerts", window_size=30)
    now = dt.datetime.utcnow()

    security_events = [SecurityEvent(device_id="x", ts=now, threat_level=3, factor="mfa")]
    environmental_events = [
        EnvironmentalEvent(device_id="x", ts=now - dt.timedelta(seconds=5), temperature=20, humidity=0.1),
        EnvironmentalEvent(device_id="x", ts=now + dt.timedelta(seconds=5), temperature=22, humidity=0.2),
    ]

    alerts = engine.process_events(security_events, environmental_events)

    assert len(alerts) == 1
    assert alerts[0]["temperature"] == 22  # latest reading wins
