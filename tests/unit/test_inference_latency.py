from types import ModuleType, SimpleNamespace

from yosai_intel_dashboard.src.core.imports.resolver import safe_import


# Stub resilience metrics to avoid optional dependency errors
metrics_mod = ModuleType("services.resilience.metrics")
metrics_mod.circuit_breaker_state = SimpleNamespace(
    labels=lambda *a, **k: SimpleNamespace(inc=lambda: None)
)
resilience_pkg = ModuleType("services.resilience")
resilience_pkg.metrics = metrics_mod
services_pkg = ModuleType("services")
safe_import("services", services_pkg)
safe_import("services.resilience", resilience_pkg)
safe_import("services.resilience.metrics", metrics_mod)

from yosai_intel_dashboard.models.ml.base_model import BaseModel, ModelMetadata


class DummyModel(BaseModel):
    def __init__(self):
        super().__init__(metadata=ModelMetadata(name="dummy"))

    def _predict(self, data):
        return data


def test_inference_latency_recorded(monkeypatch):
    calls = []
    perf = SimpleNamespace(
        record_metric=lambda *args, **kwargs: calls.append((args, kwargs))
    )
    monkeypatch.setattr(
        "yosai_intel_dashboard.models.ml.base_model.get_performance_monitor",
        lambda: perf,
    )

    model = DummyModel()
    model.predict("foo", log_prediction=False)

    assert any(args[0] == "model.inference_latency" for args, _ in calls)
    latency = next(args[1] for args, _ in calls if args[0] == "model.inference_latency")
    assert latency >= 0

