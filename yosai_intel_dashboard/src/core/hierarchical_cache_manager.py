from __future__ import annotations

"""Simple hierarchical cache with three levels and basic metrics."""

import logging
from typing import Any, Dict, Optional

from .base_model import BaseModel


class HierarchicalCacheManager(BaseModel):
    """Manage a three-level in-memory cache and record basic stats."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Create the cache manager with optional config, DB and logger."""
        super().__init__(config, db, logger)
        self._level1: Dict[str, Any] = {}
        self._level2: Dict[str, Any] = {}
        self._level3: Dict[str, Any] = {}
        self._hits = {"l1": 0, "l2": 0, "l3": 0}
        self._misses = {"l1": 0, "l2": 0, "l3": 0}
        self._evictions = {"l1": 0, "l2": 0, "l3": 0}

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


__all__ = ["HierarchicalCacheManager"]
