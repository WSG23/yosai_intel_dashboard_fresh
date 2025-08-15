import logging
import time

import pytest

from yosai_intel_dashboard.src.database import secure_exec


def _histogram_sum(hist):
    for metric in hist.collect():
        for sample in metric.samples:
            if sample.name.endswith("_sum"):
                return sample.value
    return 0


@pytest.mark.skipif(
    secure_exec.query_execution_seconds is None,
    reason="prometheus_client is not installed",
)
def test_execute_query_records_metrics_and_logs(monkeypatch, caplog):
    class Recorder:
        def execute(self, sql, params=None):  # type: ignore[no-untyped-def]
            time.sleep(0.01)
            return []

    class NoopOptimizer:
        def optimize_query(self, sql):  # type: ignore[no-untyped-def]
            return sql

    monkeypatch.setattr(secure_exec, "_get_optimizer", lambda _: NoopOptimizer())
    conn = Recorder()
    monkeypatch.setattr(secure_exec, "SLOW_QUERY_THRESHOLD", 0.0)
    secure_exec.query_metrics.clear()

    start_sum = _histogram_sum(secure_exec.query_execution_seconds)
    with caplog.at_level(logging.WARNING):
        secure_exec.execute_query(conn, "SELECT 1")

    assert secure_exec.query_metrics, "execution time should be recorded"
    assert any("Slow query" in r.message for r in caplog.records)
    end_sum = _histogram_sum(secure_exec.query_execution_seconds)
    assert end_sum > start_sum
