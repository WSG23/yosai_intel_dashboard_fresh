from __future__ import annotations

from typing import Iterable, Optional

import logging

from confluent_kafka import Consumer, Message


logger = logging.getLogger(__name__)


class ExactlyOnceKafkaConsumer:
    """Kafka consumer with manual commits for exactly-once delivery."""

    def __init__(
        self,
        topics: Iterable[str],
        *,
        brokers: str = "localhost:9092",
        group_id: str = "analytics",
        **configs,
    ) -> None:
        base = {
            "bootstrap.servers": brokers,
            "group.id": group_id,
            "enable.auto.commit": False,
            "auto.offset.reset": "earliest",
        }
        base.update(configs)
        self._consumer = Consumer(base)
        self._consumer.subscribe(list(topics))

    def poll(self, timeout: float = 1.0) -> Optional[Message]:
        msg = self._consumer.poll(timeout)
        if msg is None or msg.error():
            return None
        return msg

    def commit(self, msg: Message) -> None:
        """Commit offsets for *msg* and re-raise on failure."""
        try:
            self._consumer.commit(msg, asynchronous=False)
        except Exception:  # noqa: BLE001
            logger.exception("Kafka commit failed")
            raise

    def close(self) -> None:
        """Commit outstanding offsets and close the consumer."""
        try:
            self._consumer.commit()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to commit offsets on close")
        try:
            self._consumer.close()
        except Exception:  # noqa: BLE001
            logger.exception("Failed to close consumer")

