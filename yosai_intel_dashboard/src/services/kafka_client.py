"""Minimal Kafka publishing client."""
from __future__ import annotations

import json
import logging
import uuid
from typing import Any

from confluent_kafka import Producer

from yosai_intel_dashboard.src.services.kafka.metrics import (
    delivery_failure_total,
    delivery_success_total,
)

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
        payload_str = json.dumps(message)
        try:
            while True:
                try:
                    self._producer.produce(
                        topic, payload_str, on_delivery=self._delivery_callback
                    )
                    break
                except BufferError:
                    # Local buffer is full, let the producer flush pending events
                    self._producer.poll(0.1)
            # Serve delivery callbacks for previously produced messages
            self._producer.poll(0)
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
