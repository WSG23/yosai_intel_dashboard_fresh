from __future__ import annotations

import logging
import sys
import types
from unittest.mock import MagicMock

# Stub confluent_kafka.avro before importing the module under test
avro_module = types.ModuleType("confluent_kafka.avro")
avro_module.AvroConsumer = MagicMock()
sys.modules.setdefault("confluent_kafka", types.ModuleType("confluent_kafka"))
sys.modules["confluent_kafka.avro"] = avro_module

from yosai_intel_dashboard.src.services.kafka_consumer import KafkaConsumer


def test_poll_returns_message() -> None:
    msg = MagicMock()
    msg.error.return_value = None
    avro_module.AvroConsumer.return_value.poll.return_value = msg

    consumer = KafkaConsumer(["topic"], brokers="b", schema_registry="s")
    assert consumer.poll() is msg


def test_poll_logs_error_and_returns_none(caplog) -> None:
    err_msg = MagicMock()
    err_msg.error.return_value = Exception("bad")
    avro_module.AvroConsumer.return_value.poll.return_value = err_msg

    consumer = KafkaConsumer(["topic"])
    with caplog.at_level(logging.ERROR):
        assert consumer.poll() is None
        assert "Consumer error" in caplog.text


def test_close_swallows_exceptions() -> None:
    instance = avro_module.AvroConsumer.return_value
    instance.commit.side_effect = Exception("fail")
    instance.close.side_effect = Exception("fail")

    consumer = KafkaConsumer(["topic"])
    consumer.close()  # should not raise

