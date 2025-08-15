import asyncio
import time
from types import SimpleNamespace

import pytest

from yosai_intel_dashboard.src.core import performance
from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from yosai_intel_dashboard.src.core.performance import PerformanceMonitor
from yosai_intel_dashboard.src.core import performance as perf_src


@pytest.mark.asyncio
async def test_allows_calls_when_closed(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    performance._performance_monitor = monitor
    perf_src._performance_monitor = monitor
    monkeypatch.setattr(
        "core.async_utils.async_circuit_breaker._get_circuit_breaker_state",
        lambda: SimpleNamespace(labels=lambda *a: SimpleNamespace(inc=lambda: None)),
    )
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

    @cb
    async def func(x):
        await asyncio.sleep(0)
        return x

    assert await func(1) == 1
    assert await cb.allows_request() is True
    names = [m.name for m in monitor.metrics]
    assert "circuit_breaker" in names


@pytest.mark.asyncio
async def test_opens_after_failure_threshold(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    performance._performance_monitor = monitor
    perf_src._performance_monitor = monitor
    monkeypatch.setattr(
        "core.async_utils.async_circuit_breaker._get_circuit_breaker_state",
        lambda: SimpleNamespace(labels=lambda *a: SimpleNamespace(inc=lambda: None)),
    )
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

    @cb
    async def fail():
        await asyncio.sleep(0)
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await fail()
    with pytest.raises(RuntimeError):
        await fail()

    assert await cb.allows_request() is False
    names = [m.name for m in monitor.metrics]
    assert "circuit_breaker" in names


@pytest.mark.asyncio
async def test_recovers_after_timeout(monkeypatch):
    t = 1000.0

    monkeypatch.setattr(time, "time", lambda: t)
    monitor = PerformanceMonitor(max_metrics=10)
    performance._performance_monitor = monitor
    perf_src._performance_monitor = monitor
    monkeypatch.setattr(
        "core.async_utils.async_circuit_breaker._get_circuit_breaker_state",
        lambda: SimpleNamespace(labels=lambda *a: SimpleNamespace(inc=lambda: None)),
    )
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=5)

    await cb.record_failure()
    assert await cb.allows_request() is False

    t += 6
    assert await cb.allows_request() is True
    await cb.record_success()
    assert await cb.allows_request() is True
