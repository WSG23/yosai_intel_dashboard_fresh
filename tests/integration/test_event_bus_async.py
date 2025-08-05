import asyncio

from yosai_intel_dashboard.src.core.callbacks.event_bus import EventBus
from yosai_intel_dashboard.src.infrastructure.callbacks.events import CallbackEvent


def test_async_subscribe_and_publish() -> None:
    bus = EventBus()
    events: list[str] = []

    async def handler(message: str) -> None:
        events.append(message)

    asyncio.run(bus.subscribe_async(CallbackEvent.BEFORE_REQUEST, handler))
    asyncio.run(bus.publish_async(CallbackEvent.BEFORE_REQUEST, "ping"))

    assert events == ["ping"]
