import sys
import types

sys.modules.pop("prometheus_client", None)
from prometheus_client import REGISTRY


class DummyProducer:
    def __init__(self, conf):
        self.flushed = False

    def produce(self, topic, value, on_delivery):
        on_delivery(None, None)

    def poll(self, timeout):
        pass

    def flush(self):
        self.flushed = True


# Inject stub before importing KafkaClient
confluent = types.ModuleType("confluent_kafka")
confluent.Producer = DummyProducer
sys.modules["confluent_kafka"] = confluent

from yosai_intel_dashboard.src.services import kafka_client as kafka_client_module
from yosai_intel_dashboard.src.services.kafka_client import KafkaClient
from yosai_intel_dashboard.src.services.kafka.metrics import (
    delivery_failure_total,
    delivery_success_total,
)


def _metric_value(name: str) -> float:
    return REGISTRY.get_sample_value(name) or 0.0


def test_publish_tracks_success(monkeypatch):
    monkeypatch.setattr(kafka_client_module, "Producer", DummyProducer)
    start_success = _metric_value("kafka_delivery_success_total")
    start_failure = _metric_value("kafka_delivery_failure_total")

    client = KafkaClient("brokers")
    client.publish("topic", "type", {"a": 1})
    client.close()

    assert _metric_value("kafka_delivery_success_total") == start_success + 1
    assert _metric_value("kafka_delivery_failure_total") == start_failure
    assert client._producer.flushed is True


def test_publish_tracks_failure(monkeypatch):
    class FailingProducer(DummyProducer):
        def produce(self, topic, value, on_delivery):
            on_delivery(Exception("boom"), None)

    monkeypatch.setattr(kafka_client_module, "Producer", FailingProducer)
    start_failure = _metric_value("kafka_delivery_failure_total")

    client = KafkaClient("brokers")
    client.publish("topic", "type", {"a": 1})
    client.close()

    assert _metric_value("kafka_delivery_failure_total") == start_failure + 1
