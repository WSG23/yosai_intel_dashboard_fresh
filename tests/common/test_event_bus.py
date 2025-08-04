from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

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


def test_event_history_immutable():
    bus = EventBus()
    bus.emit("evt", {"a": 1})
    event = bus._history[0]

    with pytest.raises(FrozenInstanceError):
        event.type = "other"  # type: ignore[misc]

    with pytest.raises(TypeError):
        event.data["a"] = 2  # type: ignore[index]
