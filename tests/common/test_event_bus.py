from __future__ import annotations

from src.common.events import EventBus, EventPublisher
from src.common.base import BaseComponent


def test_publish_and_unsubscribe():
    bus = EventBus()
    received = {}

    def handler(payload):
        received.update(payload)

    token = bus.subscribe("evt", handler)
    bus.emit("evt", {"a": 1})
    assert received == {"a": 1}

    bus.unsubscribe(token)
    received.clear()
    bus.emit("evt", {"b": 2})
    assert received == {}


def test_event_publisher_mixin():
    bus = EventBus()
    received: dict[str, int] = {}

    class Publisher(EventPublisher, BaseComponent):
        pass

    bus.subscribe("evt", lambda payload: received.update(payload))
    publisher = Publisher(event_bus=bus)
    publisher.publish_event("evt", {"c": 3})

    assert received == {"c": 3}
