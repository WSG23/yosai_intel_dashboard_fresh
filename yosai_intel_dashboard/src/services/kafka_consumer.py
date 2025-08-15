import logging
from typing import Any, Iterable, MutableMapping, Optional

from confluent_kafka.avro import AvroConsumer

try:  # pragma: no cover - tracing optional
    from opentelemetry import context as ot_context, propagate
except Exception:  # pragma: no cover - graceful fallback when tracing missing

    ot_context = propagate = None  # type: ignore

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
        self._ctx_token = None

    def poll(self, timeout: float = 1.0) -> Optional[Any]:
        """Return the next message or ``None`` if none are available."""
        msg = self._consumer.poll(timeout)
        if msg is None:
            return None
        if msg.error():
            logger.error("Consumer error: %s", msg.error())
            return None
        if propagate and ot_context:
            if self._ctx_token is not None:
                ot_context.detach(self._ctx_token)
            headers = msg.headers() or []
            carrier: MutableMapping[str, str] = {
                k: v.decode() if isinstance(v, bytes) else v for k, v in headers
            }
            ctx = propagate.extract(carrier)
            self._ctx_token = ot_context.attach(ctx)
        return msg

    def close(self) -> None:
        """Commit offsets and close the consumer."""
        try:
            self._consumer.commit()
            self._consumer.close()
        except Exception:  # pragma: no cover - best effort
            pass
        if ot_context and self._ctx_token is not None:
            try:
                ot_context.detach(self._ctx_token)
            except Exception:  # pragma: no cover - cleanup
                pass


__all__ = ["KafkaConsumer"]
