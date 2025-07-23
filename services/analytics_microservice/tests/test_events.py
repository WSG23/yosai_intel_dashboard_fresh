import logging
import types
import pathlib
import sys

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)
config_stub = types.ModuleType("config")
config_stub.get_database_config = lambda: None
sys.modules.setdefault("config", config_stub)
import importlib.util
import pytest

events_spec = importlib.util.spec_from_file_location(
    "services.analytics_microservice.src.core.events",
    SERVICES_PATH / "analytics_microservice" / "src" / "core" / "events.py",
)
events = importlib.util.module_from_spec(events_spec)
events_spec.loader.exec_module(events)  # type: ignore[arg-type]


class DummyConsumer:
    def __init__(self, *_args, **_kwargs):
        self.closed = False

    def subscribe(self, _topics):
        pass

    def poll(self, _timeout):
        return None

    def commit(self, *_args, **_kwargs):
        raise RuntimeError("boom")

    def close(self):
        self.closed = True


def test_commit_failure_logs_and_raises(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)
    monkeypatch.setattr(events, "Consumer", lambda *_a, **_k: DummyConsumer())

    consumer = events.ExactlyOnceKafkaConsumer(["t"])

    with pytest.raises(RuntimeError):
        consumer.commit(types.SimpleNamespace())

    assert any("Kafka commit failed" in r.message for r in caplog.records)


def test_close_logs_commit_failure(monkeypatch, caplog):
    caplog.set_level(logging.ERROR)
    dummy = DummyConsumer()
    monkeypatch.setattr(events, "Consumer", lambda *_a, **_k: dummy)

    consumer = events.ExactlyOnceKafkaConsumer(["t"])
    consumer.close()

    assert dummy.closed
    assert any("Failed to commit offsets on close" in r.message for r in caplog.records)
