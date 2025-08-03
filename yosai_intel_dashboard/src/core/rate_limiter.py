from __future__ import annotations

"""Redis backed sliding window rate limiter."""

import logging
import os
import time
import uuid
from typing import Dict, List, Optional

import redis.asyncio as redis

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter using Redis sorted sets with sliding window semantics."""

    def __init__(
        self,
        redis_client: Optional[redis.Redis] = None,
        tier_config: Optional[Dict[str, Dict[str, int]]] = None,
        window: int = 60,
        limit: int = 60,
        burst: int = 0,
        key_prefix: str = "rl:",
    ) -> None:
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.default_config = {"window": window, "limit": limit, "burst": burst}
        self.tier_config = tier_config or {}
        self._memory: Dict[str, List[float]] = {}

    def _get_config(self, tier: str) -> Dict[str, int]:
        return self.tier_config.get(tier, self.default_config)

    def _build_key(self, identifier: str, tier: str) -> str:
        return f"{self.key_prefix}{tier}:{identifier}"

    async def is_allowed(
        self, identifier: Optional[str], ip: str, tier: str = "default"
    ) -> Dict[str, float]:
        """Check rate limit for *identifier* or *ip* within given *tier*.

        Returns a mapping with ``allowed`` flag, ``remaining`` quota and seconds
        until reset. ``retry_after`` is included when the request is rejected.
        """

        ident = identifier or ip
        cfg = self._get_config(tier)
        window = cfg["window"]
        limit = cfg["limit"]
        burst = cfg.get("burst", 0)
        now = time.time()
        key = self._build_key(ident, tier)

        if self.redis is not None:
            member = f"{now}-{uuid.uuid4().hex}"
            try:
                pipe = self.redis.pipeline()
                pipe.zadd(key, {member: now})
                pipe.zremrangebyscore(key, 0, now - window)
                pipe.zcard(key)
                pipe.zrange(key, 0, 0, withscores=True)
                pipe.expire(key, window)
                _, _, count, oldest, _ = await pipe.execute()
                count = int(count)
                allowed = count <= limit + burst
                if not allowed:
                    await self.redis.zrem(key, member)
                remaining = max(0, limit + burst - (count if allowed else count - 1))
                if oldest:
                    oldest_score = float(oldest[0][1])
                    reset = max(0, window - (now - oldest_score))
                else:
                    reset = window
                result = {
                    "allowed": allowed,
                    "remaining": remaining,
                    "reset": reset,
                }
                if not allowed:
                    result["retry_after"] = reset
                return result
            except Exception as exc:  # pragma: no cover - best effort
                logger.warning("Redis rate limit check failed for %s: %s", key, exc)

        # Fallback to in-memory implementation
        timestamps = self._memory.setdefault(key, [])
        cutoff = now - window
        timestamps[:] = [ts for ts in timestamps if ts > cutoff]
        allowed = len(timestamps) < limit + burst
        if allowed:
            timestamps.append(now)
        remaining = max(0, limit + burst - len(timestamps))
        if timestamps:
            reset = max(0, window - (now - timestamps[0]))
        else:
            reset = window
        result = {"allowed": allowed, "remaining": remaining, "reset": reset}
        if not allowed:
            result["retry_after"] = reset
        return result


async def create_rate_limiter(
    tier_config: Optional[Dict[str, Dict[str, int]]] = None,
    window: int = 60,
    limit: int = 60,
    burst: int = 0,
) -> RateLimiter:
    """Factory to create :class:`RateLimiter` with Redis connection."""
    redis_client: Optional[redis.Redis] = None
    try:
        redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
        )
        await redis_client.ping()
    except Exception:  # pragma: no cover - best effort
        redis_client = None
    return RateLimiter(redis_client, tier_config, window, limit, burst)

