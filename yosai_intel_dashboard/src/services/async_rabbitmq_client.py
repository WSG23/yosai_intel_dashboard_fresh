"""Async RabbitMQ client using connection and channel pools."""

from __future__ import annotations

import json
from typing import Any

try:
    from aio_pika import Message, connect_robust  # type: ignore
    from aio_pika.pool import Pool  # type: ignore
except Exception:  # pragma: no cover - optional dependency may be missing
    Message = Any  # type: ignore
    connect_robust = None  # type: ignore
    Pool = Any  # type: ignore


class RabbitMQPool:
    """Minimal publisher built on top of ``aio_pika`` pools."""

    def __init__(self, url: str, *, pool_size: int = 10) -> None:
        if connect_robust is None:  # pragma: no cover - optional dependency missing
            raise RuntimeError("aio_pika is required for RabbitMQPool")
        self._url = url
        self._connection_pool: Pool = Pool(self._connect, max_size=pool_size)
        self._channel_pool: Pool = Pool(self._get_channel, max_size=pool_size)

    async def _connect(self):
        return await connect_robust(self._url)  # type: ignore[arg-type]

    async def _get_channel(self):
        async with self._connection_pool.acquire() as connection:
            return await connection.channel()

    async def declare_queue(self, name: str) -> None:
        async with self._channel_pool.acquire() as channel:
            await channel.declare_queue(name, durable=True)

    async def publish(self, queue: str, message: Any) -> None:
        body = json.dumps(message).encode()
        async with self._channel_pool.acquire() as channel:
            await channel.default_exchange.publish(Message(body), routing_key=queue)

    async def close(self) -> None:
        await self._channel_pool.close()
        await self._connection_pool.close()


__all__ = ["RabbitMQPool"]
