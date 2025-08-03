from __future__ import annotations

"""Utilities for predictive cache warming."""

import asyncio
import json
import logging
from collections import Counter
from pathlib import Path
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

    # ------------------------------------------------------------------
    def save(self, path: str | Path) -> None:
        """Persist usage counters to *path* in JSON format."""
        Path(path).write_text(json.dumps(self._counter))

    # ------------------------------------------------------------------
    def load(self, path: str | Path) -> None:
        """Load usage counters from *path* if it exists."""
        p = Path(path)
        if p.exists():
            data = json.loads(p.read_text() or "{}")
            self._counter = Counter(data)


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
            if await self.cache.get(key) is None:
                value = await loop.run_in_executor(None, self.loader, key)
                await self.cache.set(key, value, level=1)
                await self.cache.set(key, value, level=2)

        await asyncio.gather(*(_load(k) for k in keys))

    # ------------------------------------------------------------------
    async def warm_from_file(self, path: str | Path, limit: int = 5) -> None:
        """Warm caches using usage statistics stored at *path*."""
        self.analyzer.load(path)
        await self.warm(limit)

    # ------------------------------------------------------------------
    def save_stats(self, path: str | Path) -> None:
        """Persist usage statistics for future startups."""
        self.analyzer.save(path)


__all__ = ["UsagePatternAnalyzer", "IntelligentCacheWarmer"]
