import asyncio
import time

from shared.events.bus import EventBus


def test_event_delivery() -> None:
    bus = EventBus()
    events: list[int] = []

    async def handler(value: int) -> None:
        events.append(value)

    asyncio.run(bus.subscribe_async("ping", handler))
    asyncio.run(bus.publish_async("ping", 1))

    assert events == [1]


def test_throttling() -> None:
    bus = EventBus()
    calls: list[int] = []

    def handler(value: int) -> None:
        calls.append(value)

    bus.subscribe("ping", handler, throttle=0.05)
    bus.publish("ping", 1)
    bus.publish("ping", 2)

    assert calls == [1]

    time.sleep(0.06)
    bus.publish("ping", 3)
    assert calls == [1, 3]
