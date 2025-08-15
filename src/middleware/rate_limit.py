import asyncio
import os
from typing import Callable, Dict, Optional

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

try:
    import redis
except Exception:  # pragma: no cover - redis optional
    redis = None  # type: ignore


class RedisRateLimiter:
    """Simple Redis backed rate limiter supporting tiers and bursts."""

    def __init__(
        self,
        client: "redis.Redis",
        tiers: Dict[str, Dict[str, int]],
        *,
        window: int = 60,
        fallback: bool = True,
    ) -> None:
        self.redis = client
        self.tiers = tiers
        self.window = window
        self.fallback = fallback

    def _limits(self, tier: str) -> Dict[str, int]:
        return self.tiers.get(tier, self.tiers.get("default", {"limit": 60, "burst": 0}))

    def hit(self, user: Optional[str], ip: str, tier: str = "default") -> Dict[str, int | bool | None]:
        key = f"rl:{tier}:{user or ip}"
        limits = self._limits(tier)
        limit = int(limits.get("limit", 60))
        burst = int(limits.get("burst", 0))
        max_allowed = limit + burst
        try:
            pipe = self.redis.pipeline()
            pipe.incr(key, 1)
            pipe.expire(key, self.window)
            count, _ = pipe.execute()
            allowed = count <= max_allowed
            remaining = max(max_allowed - count, 0)
            retry_after = None
            if not allowed:
                ttl = self.redis.ttl(key)
                retry_after = ttl if ttl > 0 else self.window
            return {
                "allowed": allowed,
                "limit": max_allowed,
                "remaining": remaining,
                "retry_after": retry_after,
            }
        except Exception:
            if self.fallback:
                # fail-open
                return {
                    "allowed": True,
                    "limit": max_allowed,
                    "remaining": max_allowed,
                    "retry_after": None,
                }
            raise


def _default_identifier(request: Request) -> Optional[str]:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1]
    return None


def _default_tier(_: Request) -> str:
    return "default"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware enforcing rate limits and injecting headers."""

    def __init__(
        self,
        app,
        limiter: RedisRateLimiter,
        *,
        identifier_getter: Callable[[Request], Optional[str]] | None = None,
        tier_getter: Callable[[Request], str] | None = None,
    ) -> None:
        super().__init__(app)
        self.limiter = limiter
        self.identifier_getter = identifier_getter or _default_identifier
        self.tier_getter = tier_getter or _default_tier

    async def dispatch(self, request: Request, call_next) -> Response:
        user = self.identifier_getter(request)
        ip = request.client.host if request.client else "unknown"
        tier = self.tier_getter(request)
        result = await asyncio.to_thread(self.limiter.hit, user, ip, tier)
        headers = {
            "X-RateLimit-Limit": str(result["limit"]),
            "X-RateLimit-Remaining": str(result["remaining"]),
        }
        retry = result.get("retry_after")
        if not result["allowed"]:
            if retry is not None:
                headers["Retry-After"] = str(int(retry))
            return JSONResponse(
                status_code=429,
                content={"detail": "rate limit exceeded"},
                headers=headers,
            )
        response = await call_next(request)
        if retry is not None:
            headers["Retry-After"] = str(int(retry))
        for k, v in headers.items():
            response.headers[k] = v
        return response


def rate_limit(
    limiter: RedisRateLimiter,
    *,
    tier: str = "default",
    identifier_getter: Callable[[], Optional[str]] | None = None,
) -> Callable:
    """Flask decorator enforcing rate limits and adding headers."""

    def decorator(func: Callable) -> Callable:
        from functools import wraps
        from flask import request, make_response

        @wraps(func)
        def wrapper(*args, **kwargs):
            user = None
            if identifier_getter is not None:
                user = identifier_getter()
            else:
                auth = request.headers.get("Authorization", "")
                if auth.startswith("Bearer "):
                    user = auth.split(" ", 1)[1]
            ip = request.remote_addr or "unknown"
            result = limiter.hit(user, ip, tier)
            headers = {
                "X-RateLimit-Limit": str(result["limit"]),
                "X-RateLimit-Remaining": str(result["remaining"]),
            }
            retry = result.get("retry_after")
            if not result["allowed"]:
                if retry is not None:
                    headers["Retry-After"] = str(int(retry))
                resp = make_response(({"detail": "rate limit exceeded"}, 429))
                for k, v in headers.items():
                    resp.headers[k] = v
                return resp
            resp = make_response(func(*args, **kwargs))
            if retry is not None:
                headers["Retry-After"] = str(int(retry))
            for k, v in headers.items():
                resp.headers[k] = v
            return resp

        return wrapper

    return decorator
