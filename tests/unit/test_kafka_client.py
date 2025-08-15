from __future__ import annotations

import sys
import types
from pathlib import Path
from unittest.mock import MagicMock
import importlib.util

import opentelemetry.trace as trace

# Stub confluent_kafka before loading KafkaClient
kafka_module = types.ModuleType("confluent_kafka")
kafka_module.Producer = MagicMock()
sys.modules["confluent_kafka"] = kafka_module

spec = importlib.util.spec_from_file_location(
    "kafka_client_module",
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard/src/services/kafka_client.py",
)
kc_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kc_mod)
KafkaClient = kc_mod.KafkaClient


def test_publish_injects_traceparent_header() -> None:
    import opentelemetry.trace as trace_mod

    tracer = trace_mod.get_tracer(__name__)
    with tracer.start_as_current_span("root"):
        client = KafkaClient("brokers")
        client.publish("topic", "task", {"foo": "bar"})
        headers = kafka_module.Producer.return_value.produce.call_args[1]["headers"]
        assert any(key == "traceparent" for key, _ in headers)
