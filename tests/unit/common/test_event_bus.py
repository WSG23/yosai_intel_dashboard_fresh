from __future__ import annotations
import os
import types
from pathlib import Path

from shared.events.bus import EventBus, EventPublisher
from src.common.base import BaseComponent
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

repo_root = Path(os.getenv("REPO_ROOT") or Path(__file__).resolve().parents[3])

services_stub = types.ModuleType("yosai_intel_dashboard.src.services")
services_stub.__path__ = [
    str(repo_root / "yosai_intel_dashboard" / "src" / "services")
]
safe_import("yosai_intel_dashboard.src.services", services_stub)
from yosai_intel_dashboard.src.services.publishing_service import PublishingService


def test_publish_and_unsubscribe():
    bus = EventBus()
    received = {}

    def handler(payload):
        received.update(payload)

    bus.subscribe("evt", handler)
    bus.publish("evt", {"a": 1})
    assert received == {"a": 1}

    bus.unsubscribe("evt", handler)
    received.clear()
    bus.publish("evt", {"b": 2})
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


def test_publishing_service():
    bus = EventBus()
    received = []
    bus.subscribe("evt", lambda payload: received.append(payload))
    publisher = PublishingService(bus)
    publisher.publish({"d": 4}, event="evt")
    assert received == [{"d": 4}]


def test_publishing_service_without_bus():
    publisher = PublishingService()
    received = []
    publisher.event_bus.subscribe("evt", lambda payload: received.append(payload))
    publisher.publish({"e": 5}, event="evt")
    assert received == [{"e": 5}]
