from __future__ import annotations

import sys
import types
from unittest.mock import MagicMock
import contextlib

# Stub confluent_kafka before loading KafkaClient
kafka_module = types.ModuleType("confluent_kafka")
kafka_module.Producer = MagicMock()
sys.modules["confluent_kafka"] = kafka_module

trace_module = types.SimpleNamespace(
    get_tracer=lambda name: types.SimpleNamespace(
        start_as_current_span=lambda name: contextlib.nullcontext()
    )
)
sys.modules["opentelemetry.trace"] = trace_module

def _propagate(headers):
    headers["traceparent"] = "dummy"

sys.modules["tracing"] = types.SimpleNamespace(propagate_context=_propagate)

from yosai_intel_dashboard.src.services import kafka_client as kc_mod

KafkaClient = kc_mod.KafkaClient


def test_publish_injects_traceparent_header() -> None:
    tracer = trace_module.get_tracer(__name__)
    with tracer.start_as_current_span("root"):
        client = KafkaClient("brokers")
        client.publish("topic", "task", {"foo": "bar"})
        headers = kafka_module.Producer.return_value.produce.call_args[1]["headers"]
        assert any(key == "traceparent" for key, _ in headers)
