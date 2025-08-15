# tests need minimal stubs for heavy dependencies
import sys
import types
from dataclasses import dataclass

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Stub out heavy dependencies before importing the service
safe_import('yosai_intel_dashboard.src.infrastructure.config', types.SimpleNamespace()
    get_monitoring_config=lambda: {}
)

@dataclass
class _Metrics:
    accuracy: float
    precision: float
    recall: float


def _get_monitor():
    return types.SimpleNamespace(detect_drift=lambda metrics: False, baseline=None)

sys.modules[
    "yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor"
] = types.SimpleNamespace(ModelMetrics=_Metrics, get_model_performance_monitor=_get_monitor)

sys.modules[
    "yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.model_metrics"
] = types.SimpleNamespace(update_model_metrics=lambda metrics: None)

sys.modules[
    "yosai_intel_dashboard.models.ml.model_registry"
] = types.SimpleNamespace(ModelRegistry=object)

from yosai_intel_dashboard.src.infrastructure.monitoring import (
    model_monitoring_service as mms,
)


class DummyRec:
    def __init__(self, name: str):
        self.name = name
        self.version = "1"
        self.is_active = True
        self.metrics = {"accuracy": 1.0, "precision": 1.0, "recall": 1.0}


class DummyRegistry:
    def __init__(self):
        self._records = [DummyRec("a"), DummyRec("b")]

    def list_models(self):
        return self._records


def test_evaluation_continues_on_failure(monkeypatch):
    registry = DummyRegistry()
    service = mms.ModelMonitoringService(registry)

    calls = {"count": 0}

    def failing_update(metrics):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("boom")

    monkeypatch.setattr(mms, "update_model_metrics", failing_update)
    monkeypatch.setattr(mms.time, "sleep", lambda s: None)

    service.evaluate_active_models()
    # called multiple times due to retries and second model
    assert calls["count"] > 1
