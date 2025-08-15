import os
import sys
from types import ModuleType, SimpleNamespace

from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Stubs to avoid heavy dependency imports
metrics_mod = ModuleType("services.resilience.metrics")
metrics_mod.circuit_breaker_state = SimpleNamespace(
    labels=lambda *a, **k: SimpleNamespace(inc=lambda: None)
)
resilience_pkg = ModuleType("services.resilience")
resilience_pkg.metrics = metrics_mod
services_pkg = ModuleType("services")

perf_mod = sys.modules.get("core.performance", ModuleType("core.performance"))
perf_mod.MetricType = SimpleNamespace(FILE_PROCESSING="file", EXECUTION_TIME="exec")
perf_mod.get_performance_monitor = lambda: SimpleNamespace(record_metric=lambda *a, **k: None)
sys.modules["core.performance"] = perf_mod
sys.modules["yosai_intel_dashboard.src.core.performance"] = perf_mod

prom_mod = ModuleType("monitoring.prometheus.model_metrics")
prom_mod.update_model_metrics = lambda *a, **k: None
prom_mod.start_model_metrics_server = lambda *a, **k: None

model_registry_stub = ModuleType("model_registry")
model_registry_stub.ModelRecord = object
model_registry_stub.ModelRegistry = object
pipeline_stub = ModuleType("pipeline_contract")
pipeline_stub.preprocess_events = lambda *a, **k: None
security_stub = ModuleType("security_models")
security_stub.TrainResult = object
security_stub.train_access_anomaly_iforest = lambda *a, **k: None
security_stub.train_online_threat_detector = lambda *a, **k: None
security_stub.train_predictive_maintenance_lstm = lambda *a, **k: None
security_stub.train_risk_scoring_xgboost = lambda *a, **k: None
security_stub.train_user_clustering_dbscan = lambda *a, **k: None

safe_import("monitoring.prometheus.model_metrics", prom_mod)
safe_import("yosai_intel_dashboard.src.infrastructure.monitoring.prometheus.model_metrics", prom_mod)

safe_import("services", services_pkg)
safe_import("yosai_intel_dashboard.src.services", services_pkg)
safe_import("services.resilience", resilience_pkg)
safe_import("yosai_intel_dashboard.src.services.resilience", resilience_pkg)
safe_import("services.resilience.metrics", metrics_mod)
safe_import("yosai_intel_dashboard.src.services.resilience.metrics", metrics_mod)

safe_import("yosai_intel_dashboard.models.ml.model_registry", model_registry_stub)
safe_import("yosai_intel_dashboard.src.models.ml.model_registry", model_registry_stub)
safe_import("yosai_intel_dashboard.models.ml.pipeline_contract", pipeline_stub)
safe_import("yosai_intel_dashboard.src.models.ml.pipeline_contract", pipeline_stub)
safe_import("yosai_intel_dashboard.models.ml.security_models", security_stub)
safe_import("yosai_intel_dashboard.src.models.ml.security_models", security_stub)

from yosai_intel_dashboard.models.ml.base_model import BaseModel, ModelMetadata
from yosai_intel_dashboard.src.infrastructure.monitoring import (
    model_performance_monitor as mpm,
)


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
    assert event["model_version"] == model.metadata.version


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
