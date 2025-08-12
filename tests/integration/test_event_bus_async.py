import asyncio
import time

from shared.events.bus import EventBus


def test_async_subscribe_and_publish() -> None:
    bus = EventBus()
    events: list[str] = []

    async def handler(message: str) -> None:
        events.append(message)

    asyncio.run(bus.subscribe_async("event", handler))
    asyncio.run(bus.publish_async("event", "ping"))

    assert events == ["ping"]


def test_publish_concurrent_with_backpressure() -> None:
    bus = EventBus(max_concurrency=5)
    calls: list[int] = []

    async def handler(idx: int) -> None:
        await asyncio.sleep(0.05)
        calls.append(idx)

    for i in range(10):
        bus.subscribe("e", lambda i=i: handler(i))

    start = time.perf_counter()
    asyncio.run(bus.publish_async("e"))
    duration = time.perf_counter() - start

    assert len(calls) == 10
    assert 0.05 < duration < 0.15
