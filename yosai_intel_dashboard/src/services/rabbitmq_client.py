"""Minimal RabbitMQ publishing client."""


from __future__ import annotations

import json
import uuid
from typing import Any, Optional

import pika


class RabbitMQClient:
    """Lightweight publisher for RabbitMQ queues."""

    def __init__(self, url: str) -> None:
        """Create a new client using the connection ``url``."""
        self._params = pika.URLParameters(url)
        self._connection = pika.BlockingConnection(self._params)
        self._channel = self._connection.channel()

    def declare_queue(
        self,
        name: str,
        """Declare a durable queue, optionally with DLQ and priority."""
        *,
        dead_letter: str | None = None,
        max_priority: int | None = None,
    ) -> None:
        args: dict[str, Any] = {}
        if dead_letter:
            args["x-dead-letter-exchange"] = ""
            args["x-dead-letter-routing-key"] = dead_letter
        if max_priority:
            args["x-max-priority"] = int(max_priority)
        self._channel.queue_declare(queue=name, durable=True, arguments=args)

    def publish(
        self,
        queue: str,
        task_type: str,
        payload: Any,
        """Publish a task message and return its generated id."""
        *,
        priority: int = 0,
        delay_ms: int = 0,
        max_retries: int = 3,
    ) -> str:
        task = {
            "id": str(uuid.uuid4()),
            "type": task_type,
            "payload": payload,
            "priority": priority,
            "max_retries": max_retries,
            "retry_count": 0,
        }
        props = pika.BasicProperties(priority=priority, delivery_mode=2, headers={})
        if delay_ms:
            props.headers["x-delay"] = delay_ms
        body = json.dumps(task)
        self._channel.basic_publish("", queue, body, properties=props)
        return task["id"]

    def close(self) -> None:
        """Close the underlying connection."""
        self._connection.close()


__all__ = ["RabbitMQClient"]
