"""Kafka producer with Avro serialization."""

from __future__ import annotations

import io
import logging
import struct
import threading
import time
from typing import Any, Dict, Optional, Tuple

from fastavro import parse_schema, schemaless_writer

try:  # pragma: no cover - optional dependency
    from confluent_kafka import Producer
except Exception:  # pragma: no cover - fallback stub
    class Producer:  # type: ignore
        def __init__(self, *args, **kwargs) -> None:
            pass

        def produce(self, *args, **kwargs) -> None:
            raise RuntimeError("down")

        def poll(self, timeout: float) -> None:
            pass

        def list_topics(self, timeout: float = 5) -> None:
            raise RuntimeError("down")

        def flush(self, timeout: float | None = None) -> None:
            pass
from yosai_intel_dashboard.src.infrastructure.config.circuit_breaker import (
    CircuitBreaker,
)
from yosai_intel_dashboard.src.services.common.schema_registry import (
    SchemaRegistryClient,
)
from yosai_intel_dashboard.src.services.resilience.metrics import (
    dependency_recovery_attempts,
    dependency_recovery_successes,
)

from .metrics import serialization_errors_total

logger = logging.getLogger(__name__)


class AvroProducer:
    """Produce messages encoded with Avro schemas from Schema Registry."""

    def __init__(
        self,
        *,
        brokers: str = "localhost:9092",
        schema_registry: str = "http://localhost:8081",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        check_interval: float = 30.0,
        **configs: Any,
    ) -> None:
        self._config = {"bootstrap.servers": brokers, **configs}
        self._producer = Producer(self._config)
        self._registry = SchemaRegistryClient(schema_registry)
        self._schema_cache: Dict[str, Tuple[Any, Any]] = {}
        self.circuit_breaker = CircuitBreaker(failure_threshold, recovery_timeout)
        self._interval = check_interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._monitor, daemon=True)
        self._thread.start()

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

    # ------------------------------------------------------------------
    def _monitor(self) -> None:
        while not self._stop.is_set():
            if self.circuit_breaker.state != "open":
                time.sleep(self._interval)
                continue
            dependency_recovery_attempts.labels("kafka").inc()
            try:
                self._producer.list_topics(timeout=5)
            except Exception:
                logger.warning("Kafka producer recovery attempt failed")
            else:
                dependency_recovery_successes.labels("kafka").inc()
                self.circuit_breaker.reset()
                self._producer = Producer(self._config)
                logger.info("Kafka producer recovered")
            time.sleep(self._interval)

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

        def _send() -> None:
            self._producer.produce(topic, payload, key=key, on_delivery=_delivery)
            self._producer.poll(0)

        self.circuit_breaker.call(_send)

    def flush(self, timeout: float | None = None) -> None:
        def _flush() -> None:
            self._producer.flush(timeout)

        self.circuit_breaker.call(_flush)

    def close(self) -> None:
        self._stop.set()
        self._thread.join(timeout=1)
        try:
            self._producer.flush()
        except Exception:
            pass


__all__ = ["AvroProducer"]
