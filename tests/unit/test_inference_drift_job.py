from yosai_intel_dashboard.src.infrastructure.monitoring.inference_drift_job import (
    InferenceDriftJob,
)


class DummyRecord:
    def __init__(self, metrics, active=True):
        self.metrics = metrics
        self.is_active = active


class DummyRegistry:
    def list_models(self):
        return [DummyRecord({"accuracy": 0.9, "precision": 0.8, "recall": 0.85})]


class DummyMonitor:
    def __init__(self, acc, prec, rec):
        self.aggregated_metrics = {
            "model.accuracy": [acc],
            "model.precision": [prec],
            "model.recall": [rec],
        }


def test_drift_alert(monkeypatch):
    registry = DummyRegistry()
    job = InferenceDriftJob(registry, drift_threshold=0.1)
    alerts = []
    monkeypatch.setattr(job.dispatcher, "send_alert", lambda msg: alerts.append(msg))
    monkeypatch.setattr(
        "monitoring.inference_drift_job.get_performance_monitor",
        lambda: DummyMonitor(0.6, 0.6, 0.6),
    )
    job.evaluate_drift()
    assert alerts


def test_no_drift(monkeypatch):
    registry = DummyRegistry()
    job = InferenceDriftJob(registry, drift_threshold=0.5)
    alerts = []
    monkeypatch.setattr(job.dispatcher, "send_alert", lambda msg: alerts.append(msg))
    monkeypatch.setattr(
        "monitoring.inference_drift_job.get_performance_monitor",
        lambda: DummyMonitor(0.88, 0.79, 0.86),
    )
    job.evaluate_drift()
    assert not alerts
