import asyncio
import time

import importlib
import sys

import pytest
from fastapi import FastAPI
from flask import Flask

# Ensure real httpx is used instead of test stubs
sys.modules.pop("httpx", None)
httpx = importlib.import_module("httpx")
AsyncClient = httpx.AsyncClient
ASGITransport = httpx.ASGITransport

from middleware.rate_limit import RateLimitMiddleware, RedisRateLimiter, rate_limit


class MemoryRedis:
    def __init__(self):
        self.data = {}
        self.expiry = {}

    class _Pipe:
        def __init__(self, parent):
            self.parent = parent
            self.ops = []

        def incr(self, key, amount):
            self.ops.append(("incr", key, amount))

        def expire(self, key, ttl):
            self.ops.append(("expire", key, ttl))

        def execute(self):
            results = []
            for op, key, val in self.ops:
                if op == "incr":
                    current = self.parent.data.get(key, 0) + val
                    self.parent.data[key] = current
                    results.append(current)
                elif op == "expire":
                    self.parent.expiry[key] = time.time() + val
                    results.append(True)
            return results

    def pipeline(self):
        return MemoryRedis._Pipe(self)

    def ttl(self, key):
        if key not in self.expiry:
            return -1
        return max(int(self.expiry[key] - time.time()), 0)

    def flushall(self):
        self.data.clear()
        self.expiry.clear()


def header(user: str, tier: str | None = None):
    h = {"Authorization": f"Bearer {user}"}
    if tier:
        h["X-Tier"] = tier
    return h


@pytest.mark.asyncio
async def test_fastapi_per_user():
    r = MemoryRedis()
    limiter = RedisRateLimiter(r, {"default": {"limit": 1, "burst": 0}})
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limiter=limiter)

    @app.get("/")
    async def root():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/", headers=header("u1"))).status_code == 200
        assert (await client.get("/", headers=header("u1"))).status_code == 429
        assert (await client.get("/", headers=header("u2"))).status_code == 200


@pytest.mark.asyncio
async def test_fastapi_tier_and_burst():
    r = MemoryRedis()
    tiers = {"default": {"limit": 1, "burst": 0}, "pro": {"limit": 2, "burst": 0}}
    limiter = RedisRateLimiter(r, tiers)
    app = FastAPI()
    app.add_middleware(
        RateLimitMiddleware,
        limiter=limiter,
        tier_getter=lambda req: req.headers.get("X-Tier", "default"),
    )

    @app.get("/")
    async def root():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/", headers=header("u1", "pro"))).status_code == 200
        assert (await client.get("/", headers=header("u1", "pro"))).status_code == 200
        assert (await client.get("/", headers=header("u1", "pro"))).status_code == 429

    # Burst behaviour
    r.flushall()
    limiter2 = RedisRateLimiter(r, {"default": {"limit": 1, "burst": 1}})
    app2 = FastAPI()
    app2.add_middleware(RateLimitMiddleware, limiter=limiter2)

    @app2.get("/")
    async def r2():
        return {"ok": True}

    transport2 = ASGITransport(app=app2)
    async with AsyncClient(transport=transport2, base_url="http://test2") as c2:
        assert (await c2.get("/", headers=header("u3"))).status_code == 200
        assert (await c2.get("/", headers=header("u3"))).status_code == 200
        assert (await c2.get("/", headers=header("u3"))).status_code == 429


class BrokenRedis:
    def pipeline(self):
        raise Exception("down")

    def ttl(self, key):  # pragma: no cover - never used
        return -1


@pytest.mark.asyncio
async def test_fastapi_fallback():
    limiter = RedisRateLimiter(BrokenRedis(), {"default": {"limit": 1}}, fallback=True)
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, limiter=limiter)

    @app.get("/")
    async def root():
        return {"ok": True}

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        assert (await client.get("/", headers=header("u1"))).status_code == 200


def test_flask_rate_limit_and_fallback():
    r = MemoryRedis()
    limiter = RedisRateLimiter(r, {"default": {"limit": 1, "burst": 1}})
    app = Flask(__name__)

    @app.route("/")
    @rate_limit(limiter)
    def index():  # pragma: no cover - executed via test client
        return "ok"

    client = app.test_client()
    assert client.get("/", headers=header("u1")).status_code == 200
    assert client.get("/", headers=header("u1")).status_code == 200
    assert client.get("/", headers=header("u1")).status_code == 429

    # Fallback client
    fail_limiter = RedisRateLimiter(BrokenRedis(), {"default": {"limit": 1}}, fallback=True)
    app2 = Flask(__name__)

    @app2.route("/")
    @rate_limit(fail_limiter)
    def idx():  # pragma: no cover - executed via test client
        return "ok"

    client2 = app2.test_client()
    assert client2.get("/", headers=header("u9")).status_code == 200
