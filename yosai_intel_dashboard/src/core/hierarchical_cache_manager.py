from __future__ import annotations

"""Three-level hierarchical cache manager.

This implementation coordinates an in-memory L1 cache, a Redis based L2 cache
and a disk backed L3 cache. Items are automatically promoted and demoted
between levels based on access frequency and memory pressure.
"""

import json
import logging
import os
import shelve
import threading
import time
from collections import OrderedDict, defaultdict
from dataclasses import dataclass
from typing import Any, Dict, Optional

import redis

from .base_model import BaseModel


@dataclass
class HierarchicalCacheConfig:
    """Configuration for :class:`HierarchicalCacheManager`.

    Values are loaded from environment variables with sensible defaults.
    """

    type: str = "hierarchical"
    l1_size: int = int(os.getenv("CACHE_L1_SIZE", "1024"))
    l2_host: str = os.getenv("CACHE_L2_HOST", "localhost")
    l2_port: int = int(os.getenv("CACHE_L2_PORT", "6379"))
    l2_ttl: int = int(os.getenv("CACHE_L2_TTL", "300"))
    l3_path: str = os.getenv("CACHE_L3_PATH", "/tmp/yosai_cache.db")
    l3_ttl: int = int(os.getenv("CACHE_L3_TTL", "3600"))


class HierarchicalCacheManager(BaseModel):
    """Manage a hierarchical cache with three storage levels."""

    _PROMOTION_THRESHOLD = 2

    def __init__(
        self,
        config: HierarchicalCacheConfig | None = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self.config = config or HierarchicalCacheConfig()

        # L1 memory cache with LRU eviction
        self._l1: "OrderedDict[str, Any]" = OrderedDict()
        # access counters used for promotion
        self._counts: Dict[str, int] = defaultdict(int)
        # per-key locks for cache_with_lock compatibility
        self._locks: Dict[str, threading.Lock] = {}

        # L2 Redis client (initialised in start)
        self._redis: Optional[redis.Redis] = None
        # L3 disk cache (shelve database)
        self._disk: Optional[shelve.DbfilenameShelf] = None

        # Automatically start so existing usages continue to work
        self.start()

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Initialise Redis connection and disk store."""

        try:
            self._redis = redis.Redis(
                host=self.config.l2_host, port=self.config.l2_port
            )
            self._redis.ping()
        except Exception as exc:  # pragma: no cover - Redis optional
            if self.logger:
                self.logger.warning(f"Redis unavailable: {exc}")
            self._redis = None

        os.makedirs(os.path.dirname(self.config.l3_path), exist_ok=True)
        self._disk = shelve.open(self.config.l3_path)

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Release resources for Redis and disk storage."""

        if self._redis is not None:
            try:
                self._redis.close()
            except Exception:  # pragma: no cover - best effort
                pass
            self._redis = None
        if self._disk is not None:
            self._disk.close()
            self._disk = None
        self.clear()

    # ------------------------------------------------------------------
    def get_lock(self, key: str) -> threading.Lock:
        """Return a threading lock for ``key``."""

        lock = self._locks.get(key)
        if lock is None:
            lock = threading.Lock()
            self._locks[key] = lock
        return lock

    # ------------------------------------------------------------------
    def get(self, key: str) -> Optional[Any]:
        """Retrieve *key* from the cache hierarchy."""

        if key in self._l1:
            self._counts[key] += 1
            value = self._l1.pop(key)
            self._l1[key] = value  # maintain LRU order
            return value

        value = self._get_l2(key)
        if value is not None:
            self._counts[key] += 1
            if self._counts[key] >= self._PROMOTION_THRESHOLD:
                self._promote_to_l1(key, value)
            return value

        value = self._get_l3(key)
        if value is not None:
            self._counts[key] += 1
            if self._counts[key] >= self._PROMOTION_THRESHOLD:
                self._set_l2(key, value)
            if self._counts[key] >= self._PROMOTION_THRESHOLD * 2:
                self._promote_to_l1(key, value)
            return value

        return None

    # ------------------------------------------------------------------
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        *,
        level: int | None = None,
    ) -> None:
        """Store *value* in selected cache levels.

        If *level* is ``None`` the value is written to all levels. When a
        specific level (1, 2 or 3) is provided only that layer is updated.
        """

        self._counts[key] = 0
        if level in (None, 1):
            self._promote_to_l1(key, value)
        if level in (None, 2):
            self._set_l2(key, value, ttl or self.config.l2_ttl)
        if level in (None, 3):
            self._set_l3(key, value, ttl or self.config.l3_ttl)

    # ------------------------------------------------------------------
    def delete(self, key: str) -> bool:
        """Remove *key* from all cache levels."""

        removed = False
        if key in self._l1:
            del self._l1[key]
            removed = True
        if self._redis is not None:
            try:
                removed = self._redis.delete(key) > 0 or removed
            except Exception:  # pragma: no cover - best effort
                pass
        if self._disk is not None and key in self._disk:
            del self._disk[key]
            removed = True
        self._counts.pop(key, None)
        self._locks.pop(key, None)
        return removed

    # ------------------------------------------------------------------
    def clear(self) -> None:
        """Clear all cached data."""

        self._l1.clear()
        self._counts.clear()
        if self._redis is not None:
            try:
                self._redis.flushdb()
            except Exception:  # pragma: no cover - best effort
                pass
        if self._disk is not None:
            for k in list(self._disk.keys()):
                del self._disk[k]
            self._disk.sync()

    # ------------------------------------------------------------------
    # Internal helper methods
    # ------------------------------------------------------------------
    def _promote_to_l1(self, key: str, value: Any) -> None:
        self._l1[key] = value
        self._l1.move_to_end(key)
        self._enforce_l1_size()

    def _enforce_l1_size(self) -> None:
        while len(self._l1) > self.config.l1_size:
            old_key, old_val = self._l1.popitem(last=False)
            # Demote evicted item to L2
            self._set_l2(old_key, old_val, self.config.l2_ttl)
            self._set_l3(old_key, old_val, self.config.l3_ttl)

    # L2 helpers --------------------------------------------------------
    def _get_l2(self, key: str) -> Optional[Any]:
        if self._redis is None:
            return None
        try:
            data = self._redis.get(key)
            if data is None:
                return None
            return json.loads(data.decode("utf-8"))
        except Exception:  # pragma: no cover - best effort
            return None

    def _set_l2(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if self._redis is None:
            return
        try:
            payload = json.dumps(value).encode("utf-8")
            if ttl:
                self._redis.setex(key, ttl, payload)
            else:
                self._redis.set(key, payload)
        except Exception:  # pragma: no cover - best effort
            pass

    # L3 helpers --------------------------------------------------------
    def _get_l3(self, key: str) -> Optional[Any]:
        if self._disk is None or key not in self._disk:
            return None
        try:
            data = json.loads(self._disk[key])
        except Exception:
            del self._disk[key]
            return None

        expiry = data.get("expiry")
        if expiry and time.time() > expiry:
            del self._disk[key]
            self._disk.sync()
            return None
        return data.get("value")

    def _set_l3(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        if self._disk is None:
            return
        expiry = time.time() + ttl if ttl else None
        record = json.dumps({"value": value, "expiry": expiry})
        self._disk[key] = record
        self._disk.sync()


__all__ = ["HierarchicalCacheConfig", "HierarchicalCacheManager"]
