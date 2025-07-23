"""Kafka consumer for Avro-encoded messages."""

from __future__ import annotations

import io
import logging
import struct
from typing import Any, Iterable, Optional

from confluent_kafka import Consumer
from fastavro import parse_schema, schemaless_reader

from services.common.schema_registry import SchemaRegistryClient

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
            logger.error("Failed to decode message: %s", exc)
            return None
        return msg

    def close(self) -> None:
        try:
            self._consumer.commit()
            self._consumer.close()
        except Exception:
            pass


__all__ = ["AvroConsumer"]
