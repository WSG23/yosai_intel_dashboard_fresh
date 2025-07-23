from __future__ import annotations

"""Utilities for predictive cache warming."""

import asyncio
import logging
from collections import Counter
from typing import Any, Callable, List, Optional

from .base_model import BaseModel
from .hierarchical_cache_manager import HierarchicalCacheManager


class UsagePatternAnalyzer(BaseModel):
    """Analyze access patterns to predict frequently used keys."""

    def __init__(
        self,
        config: Optional[Any] = None,
        db: Optional[Any] = None,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        super().__init__(config, db, logger)
        self._counter: Counter[str] = Counter()

    def record(self, key: str) -> None:
        """Record cache access for *key*."""
        self._counter[key] += 1

    def top_keys(self, limit: int = 5) -> List[str]:
        """Return the most frequently used keys."""
        return [k for k, _ in self._counter.most_common(limit)]


class IntelligentCacheWarmer:
    """Warm hierarchical caches based on usage predictions."""

    def __init__(
        self,
        cache: HierarchicalCacheManager,
        loader: Callable[[str], Any],
        analyzer: UsagePatternAnalyzer | None = None,
    ) -> None:
        self.cache = cache
        self.loader = loader
        self.analyzer = analyzer or UsagePatternAnalyzer()

    def record_usage(self, key: str) -> None:
        """Record that *key* was accessed."""
        self.analyzer.record(key)

    async def warm(self, limit: int = 5) -> None:
        """Asynchronously prefill caches for the most used keys."""
        keys = self.analyzer.top_keys(limit)
        if not keys:
            return

        loop = asyncio.get_event_loop()

        async def _load(key: str) -> None:
            if self.cache.get(key) is None:
                value = await loop.run_in_executor(None, self.loader, key)
                self.cache.set(key, value, level=1)
                self.cache.set(key, value, level=2)

        await asyncio.gather(*(_load(k) for k in keys))


__all__ = ["UsagePatternAnalyzer", "IntelligentCacheWarmer"]
