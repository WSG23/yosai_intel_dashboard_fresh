import builtins
import importlib
import sys


def test_metrics_import_without_prometheus_client(monkeypatch):
    """Module should load even when ``prometheus_client`` is absent."""
    monkeypatch.delitem(sys.modules, "prometheus_client", raising=False)
    monkeypatch.delitem(
        sys.modules, "yosai_intel_dashboard.src.database.metrics", raising=False
    )

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "prometheus_client":
            raise ImportError
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    metrics = importlib.import_module("yosai_intel_dashboard.src.database.metrics")

    assert "Counter" in metrics.__all__
    assert metrics.Counter.__module__ == "yosai_intel_dashboard.src.database.metrics"

    metrics.queries_total.inc()
    metrics.pool_utilization.set(1)
    metrics.query_execution_seconds.observe(0.1)
