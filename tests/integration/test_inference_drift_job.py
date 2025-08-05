from __future__ import annotations

"""Integration test ensuring inference drift triggers alerts."""

import sys
import types
from dataclasses import dataclass

# ---------------------------------------------------------------------------
# Stub heavy modules before importing the job under test
# ---------------------------------------------------------------------------

# Minimal monitoring config stub
config_stub = types.ModuleType("config")
config_stub.get_monitoring_config = lambda: {}
sys.modules["yosai_intel_dashboard.src.infrastructure.config"] = config_stub


# Alerting stubs
@dataclass
class AlertConfig:
    slack_webhook: str | None = None
    email: str | None = None
    webhook_url: str | None = None


class AlertDispatcher:
    def __init__(self, config: AlertConfig) -> None:  # pragma: no cover - trivial
        self.config = config

    def send_alert(self, message: str) -> None:  # pragma: no cover - replaced in tests
        pass


uem = types.ModuleType("user_experience_metrics")
uem.AlertConfig = AlertConfig
uem.AlertDispatcher = AlertDispatcher

core_monitoring = types.ModuleType("monitoring")
core_monitoring.user_experience_metrics = uem

perf = types.ModuleType("performance")
perf.get_performance_monitor = lambda: types.SimpleNamespace(aggregated_metrics={})

core_stub = types.ModuleType("core")
core_stub.monitoring = core_monitoring
core_stub.performance = perf
core_stub.__path__ = []
core_monitoring.__path__ = []
uem.__path__ = []
perf.__path__ = []

sys.modules["yosai_intel_dashboard.src.core"] = core_stub
sys.modules["yosai_intel_dashboard.src.core.monitoring"] = core_monitoring
sys.modules["yosai_intel_dashboard.src.core.monitoring.user_experience_metrics"] = uem
sys.modules["yosai_intel_dashboard.src.core.performance"] = perf


# Model metrics and registry stubs
@dataclass
class ModelMetrics:
    accuracy: float
    precision: float
    recall: float


mpm = types.ModuleType("model_performance_monitor")
mpm.ModelMetrics = ModelMetrics

infra_monitoring = types.ModuleType("monitoring")
infra_monitoring.model_performance_monitor = mpm
infra_monitoring.__path__ = []
mpm.__path__ = []

sys.modules["yosai_intel_dashboard.src.infrastructure.monitoring"] = infra_monitoring
sys.modules[
    "yosai_intel_dashboard.src.infrastructure.monitoring.model_performance_monitor"
] = mpm


class ModelRegistry:  # pragma: no cover - simple stub
    pass


ml_pkg = types.ModuleType("ml")
ml_pkg.model_registry = types.ModuleType("model_registry")
ml_pkg.model_registry.ModelRegistry = ModelRegistry
models_pkg = types.ModuleType("models")
models_pkg.ml = ml_pkg
ml_pkg.__path__ = []
models_pkg.__path__ = []
sys.modules["yosai_intel_dashboard.models"] = models_pkg
sys.modules["yosai_intel_dashboard.models.ml"] = ml_pkg
sys.modules["yosai_intel_dashboard.models.ml.model_registry"] = ml_pkg.model_registry

# ---------------------------------------------------------------------------
from yosai_intel_dashboard.src.infrastructure.monitoring.inference_drift_job import (
    InferenceDriftJob,
)


class StubRecord:
    """Model registry record with predefined metrics."""

    def __init__(self, metrics: dict[str, float]) -> None:
        self.metrics = metrics
        self.is_active = True


class StubRegistry:
    """Model registry exposing one active model."""

    def list_models(self):
        return [StubRecord({"accuracy": 0.9, "precision": 0.8, "recall": 0.85})]


class StubMonitor:
    """Performance monitor with metrics indicating drift."""

    def __init__(self) -> None:
        self.aggregated_metrics = {
            "model.accuracy": [0.6],
            "model.precision": [0.6],
            "model.recall": [0.6],
        }


def test_evaluate_drift_sends_alert(monkeypatch):
    registry = StubRegistry()
    job = InferenceDriftJob(registry, drift_threshold=0.1)
    messages: list[str] = []

    def capture_send(self, msg: str) -> None:
        messages.append(msg)

    monkeypatch.setattr(AlertDispatcher, "send_alert", capture_send)
    monkeypatch.setattr(
        "monitoring.inference_drift_job.get_performance_monitor",
        lambda: StubMonitor(),
    )

    job.evaluate_drift()

    assert messages and "Inference drift detected" in messages[0]
