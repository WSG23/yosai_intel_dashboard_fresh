import logging
from typing import Any, Dict, Generator, Optional

from yosai_intel_dashboard.src.core.interfaces import ConfigProviderProtocol
from yosai_framework.service import BaseService

logger = logging.getLogger(__name__)


class StreamingService(BaseService):
    """Manage Kafka or Pulsar streaming connections."""

    def __init__(self, config: Optional[Any] = None) -> None:
        super().__init__("streaming", "")
        self.config = getattr(config, "streaming", config)
        self.producer = None
        self.consumer = None
        self._client = None

    def initialize(self) -> bool:
        try:
            self.start()
            self._do_initialize()
            self.log.info("Service %s initialized", self.name)
            return True
        except Exception as exc:  # pragma: no cover - init error
            self.log.error("Failed to initialize service %s: %s", self.name, exc)
            return False

    def _do_initialize(self) -> None:
        if not self.config:
            raise RuntimeError("Streaming configuration not available")

        if getattr(self.config, "service_type", "kafka") == "pulsar":
            self._init_pulsar()
        else:
            self._init_kafka()

    # ------------------------------------------------------------------
    # Initialization helpers
    # ------------------------------------------------------------------
    def _init_kafka(self) -> None:
        try:
            from kafka import KafkaConsumer, KafkaProducer

            brokers = getattr(self.config, "brokers", "localhost:9092")
            topic = getattr(self.config, "topic", "events")
            group = getattr(self.config, "consumer_group", "yosai")

            self.producer = KafkaProducer(bootstrap_servers=brokers)
            self.consumer = KafkaConsumer(
                topic,
                bootstrap_servers=brokers,
                group_id=group,
                auto_offset_reset="latest",
            )
        except Exception as exc:  # pragma: no cover - runtime setup
            logger.error("Failed to initialize Kafka: %s", exc)
            raise

    def _init_pulsar(self) -> None:
        try:
            import pulsar

            brokers = getattr(self.config, "brokers", "pulsar://localhost:6650")
            topic = getattr(self.config, "topic", "events")
            group = getattr(self.config, "consumer_group", "yosai")

            self._client = pulsar.Client(brokers)
            self.producer = self._client.create_producer(topic)
            self.consumer = self._client.subscribe(topic, subscription_name=group)
        except Exception as exc:  # pragma: no cover - runtime setup
            logger.error("Failed to initialize Pulsar: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Producer/Consumer API
    # ------------------------------------------------------------------
    def publish(self, data: bytes, topic: Optional[str] = None) -> None:
        """Publish ``data`` to ``topic``."""
        target = topic or getattr(self.config, "topic", "events")
        if self.producer is None:
            raise RuntimeError("Streaming service not initialized")

        if getattr(self.config, "service_type", "kafka") == "pulsar":
            self.producer.send(data)
        else:
            self.producer.send(target, data)

    def consume(self, timeout: float = 1.0) -> Generator[bytes, None, None]:
        """Yield messages from the configured topic."""
        if self.consumer is None:
            raise RuntimeError("Streaming service not initialized")

        if getattr(self.config, "service_type", "kafka") == "pulsar":
            while True:
                msg = self.consumer.receive(timeout_millis=int(timeout * 1000))
                if msg is None:
                    break
                self.consumer.acknowledge(msg)
                yield msg.data()
        else:
            for msg in self.consumer:
                yield msg.value

    def close(self) -> None:
        """Close producer/consumer connections."""
        if self.producer:
            try:
                if getattr(self.config, "service_type", "kafka") == "pulsar":
                    self.producer.close()
                else:
                    self.producer.flush()
            except Exception:  # pragma: no cover - cleanup best effort
                pass
        if self.consumer:
            try:
                if getattr(self.config, "service_type", "kafka") == "pulsar":
                    self.consumer.close()
            except Exception:  # pragma: no cover
                pass
        if self._client:
            try:
                self._client.close()
            except Exception:  # pragma: no cover
                pass
