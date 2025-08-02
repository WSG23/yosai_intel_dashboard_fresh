from __future__ import annotations

"""Simple hierarchical cache with three levels and basic metrics."""


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
    """Manage a three-level in-memory cache and record basic stats."""


    def __init__(
        self,
        config: HierarchicalCacheConfig | None = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._level1: Dict[str, Any] = {}
        self._level2: Dict[str, Any] = {}
        self._level3: Dict[str, Any] = {}
        self._hits = {"l1": 0, "l2": 0, "l3": 0}
        self._misses = {"l1": 0, "l2": 0, "l3": 0}
        self._evictions = {"l1": 0, "l2": 0, "l3": 0}


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
        if key in self._level1:
            self._hits["l1"] += 1
            return self._level1[key]
        self._misses["l1"] += 1

        if key in self._level2:
            self._hits["l2"] += 1
            return self._level2[key]
        self._misses["l2"] += 1

        if key in self._level3:
            self._hits["l3"] += 1
            return self._level3[key]
        self._misses["l3"] += 1
        return None

    def set(self, key: str, value: Any, *, level: int = 1) -> None:
        if level == 1:
            self._level1[key] = value
        elif level == 2:
            self._level2[key] = value
        else:
            self._level3[key] = value


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
        self._evictions["l1"] += len(self._level1)
        self._evictions["l2"] += len(self._level2)
        self._evictions["l3"] += len(self._level3)
        self._level1.clear()
        self._level2.clear()
        self._level3.clear()

    def evict(self, key: str, *, level: int | None = None) -> None:
        if level is None:
            for lvl in (1, 2, 3):
                self.evict(key, level=lvl)
            return
        cache = {1: self._level1, 2: self._level2, 3: self._level3}[level]
        if key in cache:
            del cache[key]
            self._evictions[f"l{level}"] += 1

    def stats(self) -> Dict[str, Dict[str, int]]:
        return {
            "l1": {
                "hits": self._hits["l1"],
                "misses": self._misses["l1"],
                "evictions": self._evictions["l1"],
            },
            "l2": {
                "hits": self._hits["l2"],
                "misses": self._misses["l2"],
                "evictions": self._evictions["l2"],
            },
            "l3": {
                "hits": self._hits["l3"],
                "misses": self._misses["l3"],
                "evictions": self._evictions["l3"],
            },
        }



__all__ = ["HierarchicalCacheConfig", "HierarchicalCacheManager"]
