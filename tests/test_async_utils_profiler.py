import pytest

from core import performance
from core.async_utils.async_batch import async_batch
from core.async_utils.async_retry import async_retry
from core.performance import PerformanceMonitor
from yosai_intel_dashboard.src.core import performance as perf_src


@pytest.mark.asyncio
async def test_async_batch_emits_metrics(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)
    monkeypatch.setattr(perf_src, "_performance_monitor", monitor)

    async def gen():
        for i in range(3):
            yield i

    results = []
    async for b in async_batch(gen(), 2, queue_name="q", task_type="test"):
        results.append(b)

    names = [m.name for m in monitor.metrics]
    assert "async_batch" in names
    metric = next(m for m in monitor.metrics if m.name == "async_batch")
    assert metric.tags["queue"] == "q"
    assert metric.tags["task_type"] == "test"


@pytest.mark.asyncio
async def test_async_retry_emits_metrics_on_success(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)
    monkeypatch.setattr(perf_src, "_performance_monitor", monitor)
    calls = {"n": 0}

    @async_retry(max_attempts=2, queue_name="q", task_type="flaky")
    async def flaky():
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return "ok"

    assert await flaky() == "ok"
    names = [m.name for m in monitor.metrics]
    assert "async_retry" in names
    metric = next(m for m in monitor.metrics if m.name == "async_retry")
    assert metric.tags["queue"] == "q"
    assert metric.tags["task_type"] == "flaky"


@pytest.mark.asyncio
async def test_async_retry_emits_metrics_on_failure(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)
    monkeypatch.setattr(perf_src, "_performance_monitor", monitor)

    @async_retry(max_attempts=1, queue_name="q", task_type="fail")
    async def fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await fail()

    names = [m.name for m in monitor.metrics]
    assert "async_retry" in names
