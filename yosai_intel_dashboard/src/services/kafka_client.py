"""Minimal Kafka publishing client."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any, MutableMapping

from confluent_kafka import Producer

try:  # pragma: no cover - tracing optional
    from tracing import propagate_context
except Exception:  # pragma: no cover - graceful fallback when tracing missing

    def propagate_context(headers: MutableMapping[str, str]) -> None:  # type: ignore
        return None

logger = logging.getLogger(__name__)


class KafkaClient:
    """Lightweight publisher for Kafka topics."""

    def __init__(self, brokers: str) -> None:
        """Create a new client using the Kafka *brokers* string."""
        self._producer = Producer({"bootstrap.servers": brokers})

    def publish(
        self,
        topic: str,
        task_type: str,
        payload: Any,
        *,
        priority: int = 0,
        delay_ms: int = 0,
        max_retries: int = 3,
    ) -> str:
        """Publish a task message and return its generated id."""
        task_id = str(uuid.uuid4())
        message = {
            "id": task_id,
            "type": task_type,
            "payload": payload,
            "priority": priority,
            "max_retries": max_retries,
            "retry_count": 0,
        }
        headers: MutableMapping[str, str] = {}
        propagate_context(headers)
        try:
            self._producer.produce(
                topic,
                json.dumps(message),
                headers=list(headers.items()) or None,
            )
            self._producer.flush()

        except Exception:
            logger.exception("Failed to publish to Kafka")
            raise
        return task_id

    def close(self) -> None:
        """Flush outstanding messages and close producer."""
        self._producer.flush()

    @staticmethod
    def _delivery_callback(err, msg) -> None:  # pragma: no cover - signature defined by library
        """Track delivery results via Prometheus counters."""
        if err is not None:
            delivery_failure_total.inc()
        else:
            delivery_success_total.inc()


__all__ = ["KafkaClient"]
