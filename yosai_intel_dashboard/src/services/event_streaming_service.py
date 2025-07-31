"""Event streaming integration using Kafka."""

from __future__ import annotations

import json
import logging
import threading
from typing import Any, Optional

from kafka import KafkaConsumer, KafkaProducer

from config.kafka_config import KafkaConfig, from_environment
from yosai_framework.service import BaseService

logger = logging.getLogger(__name__)


class EventStreamingService:
    """Service managing Kafka producer/consumer threads."""

    def __init__(self, config: Optional[KafkaConfig] = None) -> None:
        """Create the service using ``config`` or environment settings."""
        self.service = BaseService("event-streaming", "")
        self.config = config or from_environment()
        self.producer: KafkaProducer | None = None
        self.consumer: KafkaConsumer | None = None
        self._worker: threading.Thread | None = None
        self._stop = threading.Event()
        self.topic = "access-events"

    def initialize(self) -> None:
        """Start producer and consumer threads."""
        self.service.start()
        self.producer = KafkaProducer(
            bootstrap_servers=self.config.brokers,
            value_serializer=lambda v: json.dumps(v).encode("utf-8"),
        )
        self.consumer = KafkaConsumer(
            self.topic,
            bootstrap_servers=self.config.brokers,
            group_id="yosai",
            auto_offset_reset="latest",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
        )
        self._worker = threading.Thread(target=self._consume_loop, daemon=True)
        self._stop.clear()
        self._worker.start()

    def _consume_loop(self) -> None:
        """Continuously consume messages until the service is stopped."""
        assert self.consumer is not None
        for message in self.consumer:
            if self._stop.is_set():
                break
            try:
                self.handle_message(message.value)
            except Exception as exc:  # pragma: no cover - best effort
                logger.debug("Consumer error: %s", exc)

    def handle_message(self, data: Any) -> None:  # pragma: no cover - default
        """Handle a single consumed message. Override in subclasses."""
        logger.info("Received message: %s", data)

    def publish_access_event(self, payload: dict) -> None:
        """Send a single access event payload to the configured topic."""
        if not self.producer:
            raise RuntimeError("Service not initialized")
        self.producer.send(self.topic, payload)

    def close(self) -> None:
        """Stop all threads and close Kafka connections."""
        self._stop.set()
        if self.consumer is not None:
            try:
                self.consumer.close()
            except Exception:  # pragma: no cover - cleanup
                pass
        if self.producer is not None:
            try:
                self.producer.flush()
                self.producer.close()
            except Exception:  # pragma: no cover
                pass
        if self._worker is not None:
            self._worker.join(timeout=1)
        self.service.stop()


__all__ = ["EventStreamingService"]
