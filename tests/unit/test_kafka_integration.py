import json
import queue
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

import pytest


class AccessResult(Enum):
    GRANTED = "Granted"
    DENIED = "Denied"


class BadgeStatus(Enum):
    VALID = "Valid"
    INVALID = "Invalid"


@dataclass
class AccessEvent:
    event_id: str
    timestamp: datetime
    person_id: str
    door_id: str
    badge_id: Optional[str] = None
    access_result: AccessResult = AccessResult.DENIED
    badge_status: BadgeStatus = BadgeStatus.INVALID
    door_held_open_time: float = 0.0
    entry_without_badge: bool = False
    device_status: str = "normal"
    raw_data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "timestamp": self.timestamp.isoformat(),
            "person_id": self.person_id,
            "door_id": self.door_id,
            "badge_id": self.badge_id,
            "access_result": self.access_result.value,
            "badge_status": self.badge_status.value,
            "door_held_open_time": self.door_held_open_time,
            "entry_without_badge": self.entry_without_badge,
            "device_status": self.device_status,
        }


class FakeKafkaProducer:
    def __init__(self, q: queue.Queue) -> None:
        self.q = q

    def send(self, topic: str, value: bytes) -> None:
        self.q.put((topic, value))

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


class FakeKafkaConsumer:
    def __init__(self, q: queue.Queue) -> None:
        self.q = q

    def __iter__(self):
        while True:
            try:
                topic, value = self.q.get_nowait()
            except queue.Empty:
                break
            yield type("Msg", (), {"value": value})

    def close(self) -> None:
        pass


@pytest.fixture
def kafka_queue() -> queue.Queue:
    return queue.Queue()


@pytest.fixture
def kafka_producer(kafka_queue: queue.Queue) -> FakeKafkaProducer:
    return FakeKafkaProducer(kafka_queue)


@pytest.fixture
def kafka_consumer(kafka_queue: queue.Queue) -> FakeKafkaConsumer:
    return FakeKafkaConsumer(kafka_queue)


def encode_event(event: dict) -> bytes:
    return json.dumps(event).encode("utf-8")


def decode_event(data: bytes) -> dict:
    event = json.loads(data.decode("utf-8"))
    required = {
        "event_id",
        "timestamp",
        "person_id",
        "door_id",
        "access_result",
    }
    if not required.issubset(event):
        raise ValueError("Invalid schema")
    return event


def test_produce_consume_access_event(kafka_producer, kafka_consumer):
    event = AccessEvent(
        event_id="1",
        timestamp=datetime.now(),
        person_id="p1",
        door_id="d1",
        badge_id="b1",
        access_result=AccessResult.GRANTED,
        badge_status=BadgeStatus.VALID,
    )
    kafka_producer.send("access", encode_event(event.to_dict()))
    msgs = list(kafka_consumer)
    assert len(msgs) == 1
    parsed = decode_event(msgs[0].value)
    assert parsed["event_id"] == "1"
    assert parsed["access_result"] == AccessResult.GRANTED.value


def test_invalid_schema_handling(kafka_producer, kafka_consumer):
    invalid = {"foo": "bar"}
    kafka_producer.send("access", encode_event(invalid))
    msgs = list(kafka_consumer)
    with pytest.raises(ValueError):
        for msg in msgs:
            decode_event(msg.value)


@pytest.mark.slow
@pytest.mark.performance
def test_kafka_throughput_benchmark(kafka_producer, kafka_consumer):
    start = time.time()
    for i in range(10000):
        event = {
            "event_id": str(i),
            "timestamp": time.time(),
            "person_id": "p",
            "door_id": "d",
            "access_result": AccessResult.GRANTED.value,
        }
        kafka_producer.send("access", encode_event(event))
    kafka_producer.flush()
    msgs = list(kafka_consumer)
    duration = time.time() - start
    assert len(msgs) == 10000
    throughput = len(msgs) / max(duration, 0.001)
    assert throughput > 1000
