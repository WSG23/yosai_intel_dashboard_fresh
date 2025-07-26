from __future__ import annotations

import asyncio
from typing import Any, Awaitable, Callable, Dict

from .protocols import MessageBus


class AsyncQueueClient(MessageBus):
    """In-memory async message queue used for testing."""

    def __init__(self) -> None:
        self._queues: Dict[str, asyncio.Queue[Any]] = {}

    async def publish(self, topic: str, message: Any) -> None:
        queue = self._queues.setdefault(topic, asyncio.Queue())
        await queue.put(message)

    async def subscribe(
        self, topic: str, handler: Callable[[Any], Awaitable[None]]
    ) -> None:
        queue = self._queues.setdefault(topic, asyncio.Queue())
        while True:
            msg = await queue.get()
            await handler(msg)
            queue.task_done()

