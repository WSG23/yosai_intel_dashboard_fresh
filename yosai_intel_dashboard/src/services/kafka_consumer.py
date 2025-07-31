import logging
from typing import Any, Iterable, Optional

from confluent_kafka.avro import AvroConsumer

logger = logging.getLogger(__name__)


class KafkaConsumer:
    """Simple wrapper around ``confluent_kafka``'s :class:`AvroConsumer`."""

    def __init__(
        self,
        topics: Iterable[str],
        brokers: str = "localhost:9092",
        group_id: str = "yosai",
        schema_registry: str = "http://localhost:8081",
        **configs: Any,
    ) -> None:
        base_config = {
            "bootstrap.servers": brokers,
            "schema.registry.url": schema_registry,
            "group.id": group_id,
            "auto.offset.reset": "latest",
        }
        base_config.update(configs)
        self._consumer = AvroConsumer(base_config)
        self._consumer.subscribe(list(topics))

    def poll(self, timeout: float = 1.0) -> Optional[Any]:
        """Return the next message or ``None`` if none are available."""
        msg = self._consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            logger.error("Consumer error: %s", msg.error())
            return None
        return msg

    def close(self) -> None:
        """Commit offsets and close the consumer."""
        try:
            self._consumer.commit()
            self._consumer.close()
        except Exception:  # pragma: no cover - best effort
            pass


__all__ = ["KafkaConsumer"]
