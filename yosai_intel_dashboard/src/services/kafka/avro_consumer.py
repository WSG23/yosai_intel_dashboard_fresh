"""Kafka consumer for Avro-encoded messages."""

from __future__ import annotations

import io
import logging
import struct
from typing import Any, Iterable, Optional

from fastavro import parse_schema, schemaless_reader

from confluent_kafka import Consumer, Producer
from yosai_intel_dashboard.src.infrastructure.monitoring.data_quality_monitor import (
    get_data_quality_monitor,
)
from yosai_intel_dashboard.src.services.common.schema_registry import (
    SchemaRegistryClient,
)

logger = logging.getLogger(__name__)


class AvroConsumer:
    """Consume and decode Avro messages from Kafka."""

    def __init__(
        self,
        topics: Iterable[str],
        *,
        brokers: str = "localhost:9092",
        group_id: str = "yosai",
        schema_registry: str = "http://localhost:8081",
        dead_letter_topic: str = "dead-letter",
        **configs: Any,
    ) -> None:
        self._consumer = Consumer(
            {
                "bootstrap.servers": brokers,
                "group.id": group_id,
                "auto.offset.reset": "latest",
                **configs,
            }
        )
        self._consumer.subscribe(list(topics))
        self._registry = SchemaRegistryClient(schema_registry)
        self._dlq = Producer({"bootstrap.servers": brokers})
        self._dead_letter_topic = dead_letter_topic

    def _decode(self, data: bytes) -> Any:
        if not data or data[0] != 0:
            raise ValueError("Invalid message format")
        schema_id = struct.unpack(">I", data[1:5])[0]
        info = self._registry.get_schema_by_id(schema_id)
        schema = parse_schema(info.schema)
        return schemaless_reader(io.BytesIO(data[5:]), schema)

    def poll(self, timeout: float = 1.0) -> Optional[Any]:
        msg = self._consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            logger.error("Consumer error: %s", msg.error())
            return None
        try:
            msg.decoded = self._decode(msg.value())  # type: ignore[attr-defined]
        except Exception as exc:
            get_data_quality_monitor().record_avro_failure()

            logger.error("Failed to decode message: %s", exc)
            try:
                self._dlq.produce(self._dead_letter_topic, msg.value())
                self._dlq.poll(0)
            except Exception as dlq_exc:
                logger.error("Failed to send to dead-letter topic: %s", dlq_exc)
            return None
        return msg

    def close(self) -> None:
        try:
            self._dlq.flush()
            self._consumer.commit()
            self._consumer.close()
        except Exception:
            pass


__all__ = ["AvroConsumer"]
