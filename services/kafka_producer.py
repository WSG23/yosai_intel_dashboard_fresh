import logging
from typing import Any, Dict, Optional

from confluent_kafka.avro import AvroProducer

logger = logging.getLogger(__name__)


class KafkaProducer:
    """Thin wrapper around ``confluent_kafka``'s :class:`AvroProducer`."""

    def __init__(
        self,
        brokers: str = "localhost:9092",
        schema_registry: str = "http://localhost:8081",
        **configs: Any,
    ) -> None:
        base_config: Dict[str, Any] = {
            "bootstrap.servers": brokers,
            "schema.registry.url": schema_registry,
            "enable.idempotence": True,
            "compression.type": "lz4",
            "batch.num.messages": 1000,
            "linger.ms": 5,
        }
        base_config.update(configs)
        self._producer = AvroProducer(base_config)

    def produce(
        self,
        topic: str,
        value: Dict[str, Any],
        value_schema: Any,
        key: Optional[str] = None,
        key_schema: Optional[Any] = None,
    ) -> None:
        """Send ``value`` to ``topic`` using the provided Avro schemas."""

        def _delivery_callback(err: Optional[Exception], msg: Any) -> None:
            if err:
                logger.error("Delivery failed: %s", err)
            else:
                logger.debug(
                    "Delivered message to %s [%s] at offset %s",
                    msg.topic(),
                    msg.partition(),
                    msg.offset(),
                )

        self._producer.produce(
            topic=topic,
            value=value,
            value_schema=value_schema,
            key=key,
            key_schema=key_schema,
            on_delivery=_delivery_callback,
        )
        self._producer.poll(0)

    def flush(self, timeout: float | None = None) -> None:
        """Flush pending messages."""
        self._producer.flush(timeout)

    def close(self) -> None:
        """Flush outstanding messages before shutdown."""
        try:
            self._producer.flush()
        except Exception:  # pragma: no cover - best effort
            pass


__all__ = ["KafkaProducer"]
