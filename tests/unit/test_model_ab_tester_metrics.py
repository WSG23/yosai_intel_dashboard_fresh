import os
import types

os.environ.setdefault("CACHE_TTL", "1")

from yosai_intel_dashboard.src.services.ab_testing import ModelABTester


def test_record_metrics_updates_internal_and_prom(monkeypatch, tmp_path):
    registry = types.SimpleNamespace(get_model=lambda *a, **k: None, download_artifact=lambda *a, **k: None)
    tester = ModelABTester(
        "model",
        registry,
        weights={},
        weights_file=tmp_path / "w.json",
        model_dir=tmp_path / "models",
    )

    class DummyMetric:
        def __init__(self):
            self.count = 0

        def labels(self, *a):
            return self

        def inc(self, val=1):
            self.count += val

        def observe(self, val):
            self.count += 1

    dummy = DummyMetric()
    monkeypatch.setattr(tester, "_prom_counts", dummy)
    monkeypatch.setattr(tester, "_prom_success", dummy)
    monkeypatch.setattr(tester, "_prom_latency", dummy)

    tester._record_metrics("1", True, 0.2)
    assert tester.metrics["1"]["count"] == 1
    assert tester.metrics["1"]["success"] == 1
    assert tester.metrics["1"]["latency_sum"] == 0.2
    assert dummy.count >= 2
