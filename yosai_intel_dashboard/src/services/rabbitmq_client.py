"""Minimal RabbitMQ publishing client."""

from __future__ import annotations

import json
import logging
import time
import uuid
from typing import Any, Optional

import pika

logger = logging.getLogger(__name__)


class RabbitMQClient:
    """Lightweight publisher for RabbitMQ queues with a simple circuit breaker."""

    def __init__(
        self,
        url: str,
        *,
        max_failures: int = 5,
        reset_timeout: float = 30.0,
    ) -> None:
        """Create a new client using the connection ``url``."""
        self._params = pika.URLParameters(url)
        self._connection = pika.BlockingConnection(self._params)
        self._channel = self._connection.channel()
        self._failures = 0
        self._max_failures = max_failures
        self._reset_timeout = reset_timeout
        self._cooldown_start: float | None = None

    def _check_circuit(self) -> None:
        if self._cooldown_start is not None:
            if time.monotonic() - self._cooldown_start < self._reset_timeout:
                raise RuntimeError("Circuit breaker open")
            self._cooldown_start = None
            self._failures = 0

    def declare_queue(
        self,
        name: str,
        *,
        dead_letter: str | None = None,
        max_priority: int | None = None,
    ) -> None:
        """Declare a durable queue, optionally with DLQ and priority."""
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
        *,
        priority: int = 0,
        delay_ms: int = 0,
        max_retries: int = 3,
    ) -> str:
        """Publish a task message and return its generated id."""
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
        self._check_circuit()
        try:
            self._channel.basic_publish("", queue, body, properties=props)
            self._failures = 0
            return task["id"]
        except Exception:
            self._failures += 1
            if self._failures >= self._max_failures:
                self._cooldown_start = time.monotonic()
                logger.warning(
                    "RabbitMQ circuit opened after %s failures", self._failures
                )
            raise

    def close(self) -> None:
        """Close the underlying connection."""
        self._connection.close()


__all__ = ["RabbitMQClient"]
