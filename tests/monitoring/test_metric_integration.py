from __future__ import annotations

import importlib
import os
import sys
import types
import urllib.request


class DummyService:
    def __init__(self):
        self.logged = []

    async def log_evaluation(
        self, model_name, version, metric, value, drift_type, status
    ):
        self.logged.append((model_name, version, metric, value, drift_type, status))


class DummyPublisher:
    def __init__(self, event_bus=None):
        self.event_bus = event_bus

    def publish(self, payload):
        pass


def test_prometheus_exposure_and_db_persistence(monkeypatch):
    os.environ["CACHE_TTL_SECONDS"] = "1"
    os.environ["JWKS_CACHE_TTL"] = "1"

    class _EventBus:
        def publish(self, event, payload):
            pass

        def subscribe(self, *a, **k):
            pass

    sys.modules["yosai_intel_dashboard.src.core.events"] = types.SimpleNamespace(
        EventBus=_EventBus
    )
    sys.modules["yosai_intel_dashboard.src.services.model_monitoring_service"] = (
        types.SimpleNamespace(ModelMonitoringService=DummyService)
    )
    sys.modules["yosai_intel_dashboard.src.services.publishing_service"] = (
        types.SimpleNamespace(PublishingService=DummyPublisher)
    )

    mm = importlib.import_module(
        "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.model_metrics"
    )
    service = mm._monitoring_service

    class Metrics:
        accuracy = 0.9
        precision = 0.8
        recall = 0.7
        f1 = 0.75
        latency = 12.3
        throughput = 45.6
        drift = 0.01

    port = 9234
    mm.start_model_metrics_server(port=port)
    mm.update_model_metrics(Metrics(), model_name="demo", version="1.0")

    response = urllib.request.urlopen(f"http://localhost:{port}")
    data = response.read().decode()
    assert "model_f1_score" in data
    assert "model_latency_ms" in data
    assert any(m[2] == "f1" for m in service.logged)
    assert any(m[2] == "drift" for m in service.logged)
