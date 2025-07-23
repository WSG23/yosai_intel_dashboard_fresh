from __future__ import annotations

from typing import Iterable, Optional

from confluent_kafka import Consumer, Message


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
        self._consumer.commit(msg, asynchronous=False)

    def close(self) -> None:
        try:
            self._consumer.commit()
            self._consumer.close()
        except Exception:
            pass

