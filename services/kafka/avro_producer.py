"""Kafka producer with Avro serialization."""

from __future__ import annotations

import io
import logging
import struct
from typing import Any, Dict, Optional, Tuple

from fastavro import parse_schema, schemaless_writer

from confluent_kafka import Producer
from services.common.schema_registry import SchemaRegistryClient

from .metrics import serialization_errors_total

logger = logging.getLogger(__name__)


class AvroProducer:
    """Produce messages encoded with Avro schemas from Schema Registry."""

    def __init__(
        self,
        *,
        brokers: str = "localhost:9092",
        schema_registry: str = "http://localhost:8081",
        **configs: Any,
    ) -> None:
        self._producer = Producer({"bootstrap.servers": brokers, **configs})
        self._registry = SchemaRegistryClient(schema_registry)
        self._schema_cache: Dict[str, Tuple[Any, Any]] = {}

    def _encode(self, subject: str, value: Dict[str, Any]) -> bytes:
        if subject not in self._schema_cache:
            info = self._registry.get_schema(subject)
            schema = parse_schema(info.schema)
            self._schema_cache[subject] = (info, schema)
        else:
            info, schema = self._schema_cache[subject]
        buf = io.BytesIO()
        schemaless_writer(buf, schema, value)
        return b"\x00" + struct.pack(">I", info.id) + buf.getvalue()

    def produce(
        self,
        topic: str,
        value: Dict[str, Any],
        subject: str,
        key: Optional[str] = None,
    ) -> None:
        try:
            payload = self._encode(subject, value)
        except Exception as exc:  # validation errors
            serialization_errors_total.inc()
            logger.error("Serialization failed: %s", exc)
            raise

        def _delivery(err, msg):
            if err:
                logger.error("Delivery failed: %s", err)
            else:
                logger.debug(
                    "Delivered message to %s [%s] at offset %s",
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                )

        self._producer.produce(topic, payload, key=key, on_delivery=_delivery)
        self._producer.poll(0)

    def flush(self, timeout: float | None = None) -> None:
        self._producer.flush(timeout)

    def close(self) -> None:
        try:
            self._producer.flush()
        except Exception:
            pass


__all__ = ["AvroProducer"]
