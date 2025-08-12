from __future__ import annotations

import sys
import time
import types

import asyncio


class FakeRedis:
    def __init__(self):
        self.store = {}
        self.expire_at = {}

    async def incr(self, key: str) -> int:
        self.store[key] = self.store.get(key, 0) + 1
        return self.store[key]

    async def expire(self, key: str, seconds: int) -> None:
        self.expire_at[key] = time.time() + seconds

    async def ttl(self, key: str) -> int:
        exp = self.expire_at.get(key)
        if exp is None:
            return -2
        remaining = int(exp - time.time())
        if remaining <= 0:
            self.store.pop(key, None)
            self.expire_at.pop(key, None)
            return -2
        return remaining

    async def set(self, key: str, value: int, ex: int | None = None) -> None:
        self.store[key] = value
        if ex is not None:
            self.expire_at[key] = time.time() + ex

    async def scan_iter(self, match: str | None = None):
        prefix = match[:-1] if match and match.endswith("*") else match
        for key in list(self.expire_at.keys()):
            if prefix is None or key.startswith(prefix):
                yield key

    async def delete(self, key: str) -> None:
        self.store.pop(key, None)
        self.expire_at.pop(key, None)

# Stub out heavy SecurityValidator dependency before import
validator_stub = types.ModuleType("validation.security_validator")
validator_stub.SecurityValidator = object  # type: ignore[attr-defined]
sys.modules["validation.security_validator"] = validator_stub

from yosai_intel_dashboard.src.core.security import RateLimiter



def test_rate_limiter_returns_header_fields():
    redis_client = FakeRedis()
    limiter = RateLimiter(redis_client, max_requests=2, window_minutes=1)
    result1 = asyncio.run(limiter.is_allowed("user"))
    assert result1["allowed"] is True
    assert result1["limit"] == 2
    assert result1["remaining"] == 1
    assert result1["reset"] > time.time()

    result2 = asyncio.run(limiter.is_allowed("user"))
    assert result2["allowed"] is True
    assert result2["remaining"] == 0

    result3 = asyncio.run(limiter.is_allowed("user"))
    assert result3["allowed"] is False
    assert result3["retry_after"] > 0
    assert result3["remaining"] == 0
    assert result3["limit"] == 2
