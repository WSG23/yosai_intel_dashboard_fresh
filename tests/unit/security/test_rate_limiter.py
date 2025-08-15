import time
import pytest

from yosai_intel_dashboard.src.core.security import RateLimiter

pytestmark = pytest.mark.unit


@pytest.mark.asyncio
async def test_blocking_behavior():
    limiter = RateLimiter(window=60, limit=1)
    first = await limiter.is_allowed("user", "1.1.1.1")
    assert first["allowed"] is True

    second = await limiter.is_allowed("user", "1.1.1.1")
    assert second["allowed"] is False
    assert second["retry_after"] > 0


@pytest.mark.asyncio
async def test_reset_allows_requests(monkeypatch):
    limiter = RateLimiter(window=10, limit=1)

    current = [1000.0]
    monkeypatch.setattr(time, "time", lambda: current[0])

    assert (await limiter.is_allowed("user", "1.1.1.1"))["allowed"] is True

    current[0] += 1
    blocked = await limiter.is_allowed("user", "1.1.1.1")
    assert blocked["allowed"] is False
    assert blocked["retry_after"] > 0

    current[0] += 10
    reset = await limiter.is_allowed("user", "1.1.1.1")
    assert reset["allowed"] is True


@pytest.mark.asyncio
async def test_spoofed_ip_does_not_bypass(monkeypatch):
    limiter = RateLimiter(window=60, limit=1)

    assert (await limiter.is_allowed("user", "1.1.1.1"))["allowed"] is True

    spoofed = await limiter.is_allowed("user", "9.9.9.9")
    assert spoofed["allowed"] is False
