import sys
import types
import logging
from pathlib import Path
from unittest.mock import MagicMock
import importlib.util

import opentelemetry.trace as trace

# Stub confluent_kafka.avro before loading KafkaConsumer
avro_module = types.ModuleType("confluent_kafka.avro")
avro_module.AvroConsumer = MagicMock()
sys.modules.setdefault("confluent_kafka", types.ModuleType("confluent_kafka"))
sys.modules["confluent_kafka.avro"] = avro_module

spec = importlib.util.spec_from_file_location(
    "kafka_consumer_module",
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard/src/services/kafka_consumer.py",
)
kc_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kc_mod)
KafkaConsumer = kc_mod.KafkaConsumer


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


def test_poll_extracts_trace_context() -> None:
    import opentelemetry.trace as trace_mod

    msg = MagicMock()
    msg.error.return_value = None
    trace_id = "0123456789abcdef0123456789abcdef"
    span_id = "0123456789abcdef"
    msg.headers.return_value = [("traceparent", f"00-{trace_id}-{span_id}-01")]
    avro_module.AvroConsumer.return_value.poll.return_value = msg

    consumer = KafkaConsumer(["topic"])
    consumer.poll()

    current = trace_mod.get_current_span()
    assert f"{current.get_span_context().trace_id:032x}" == trace_id

    consumer.close()
