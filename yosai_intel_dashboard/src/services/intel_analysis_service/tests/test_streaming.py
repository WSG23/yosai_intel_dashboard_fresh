from __future__ import annotations

import pathlib
import sys

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1]))

from core.graph_etl_pipeline import GraphETLPipeline  # noqa: E402
from core.streaming import KafkaETLConsumer  # noqa: E402


class DummyMessage:
    def __init__(self, value: bytes):
        self._value = value

    def error(self):
        return None

    def value(self):
        return self._value


class DummyConsumer:
    def __init__(self, message: DummyMessage):
        self._message = message
        self.subscribed = False

    def subscribe(self, topics):
        self.subscribed = True

    def poll(self, timeout):
        msg, self._message = self._message, None
        return msg


def test_streaming_processes_message():
    pipeline = GraphETLPipeline()
    msg = DummyMessage(b"2024-01-01T00:00:00Z,alice,bob,LOGIN")
    dummy_consumer = DummyConsumer(msg)
    kafka_consumer = KafkaETLConsumer({}, ["logs"], pipeline, consumer=dummy_consumer)
    snapshots = []
    kafka_consumer.run(snapshots.append, max_messages=1)
    assert snapshots and snapshots[0]["nodes"]
