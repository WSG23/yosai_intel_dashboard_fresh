import os
import sys
from types import ModuleType, SimpleNamespace

# Stub resilience metrics to avoid optional dependency errors
metrics_mod = ModuleType("services.resilience.metrics")
metrics_mod.circuit_breaker_state = SimpleNamespace(
    labels=lambda *a, **k: SimpleNamespace(inc=lambda: None)
)
resilience_pkg = ModuleType("services.resilience")
resilience_pkg.metrics = metrics_mod
services_pkg = ModuleType("services")
sys.modules.setdefault("services", services_pkg)
sys.modules.setdefault("services.resilience", resilience_pkg)
sys.modules.setdefault("services.resilience.metrics", metrics_mod)

from monitoring import model_performance_monitor as mpm
from yosai_intel_dashboard.models.ml.base_model import BaseModel, ModelMetadata


class DummyModel(BaseModel):
    def __init__(self):
        super().__init__(metadata=ModelMetadata(name="dummy"))

    def _predict(self, data):
        return {"out": data}


def test_prediction_logged(monkeypatch):
    records = []
    logger = SimpleNamespace(info=lambda msg, extra=None: records.append(extra))
    monitor = mpm.ModelPerformanceMonitor(logger=logger)
    monkeypatch.setattr(mpm, "_model_performance_monitor", monitor)

    model = DummyModel()
    model.predict("foo", log_prediction=True)

    assert records
    event = records[0]
    assert event["prediction"] == {"out": "foo"}
    assert "input_hash" in event
    assert "timestamp" in event


def test_env_toggle(monkeypatch):
    records = []
    logger = SimpleNamespace(info=lambda msg, extra=None: records.append(extra))
    monitor = mpm.ModelPerformanceMonitor(logger=logger)
    monkeypatch.setattr(mpm, "_model_performance_monitor", monitor)

    os.environ["MODEL_PREDICTION_LOGGING"] = "1"
    model = DummyModel()
    model.predict("bar")  # log_prediction defaults to None
    os.environ.pop("MODEL_PREDICTION_LOGGING")

    assert records
