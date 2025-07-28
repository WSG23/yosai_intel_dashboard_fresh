import asyncio
import time
import pytest

from core.async_utils.async_circuit_breaker import CircuitBreaker, CircuitBreakerOpen


@pytest.mark.asyncio
async def test_allows_calls_when_closed():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=10)

    @cb
    async def func(x):
        await asyncio.sleep(0)
        return x

    assert await func(1) == 1
    assert await cb.allows_request() is True


@pytest.mark.asyncio
async def test_opens_after_failure_threshold():
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


@pytest.mark.asyncio
async def test_recovers_after_timeout(monkeypatch):
    t = 1000.0

    monkeypatch.setattr(time, "time", lambda: t)
    cb = CircuitBreaker(failure_threshold=1, recovery_timeout=5)

    await cb.record_failure()
    assert await cb.allows_request() is False

    t += 6
    assert await cb.allows_request() is True
    await cb.record_success()
    assert await cb.allows_request() is True
