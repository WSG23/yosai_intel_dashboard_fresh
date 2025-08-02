from __future__ import annotations

"""Simple hierarchical cache with two levels."""

import asyncio
import inspect
import logging
from typing import Any, Callable, Dict, Optional

from .base_model import BaseModel


class HierarchicalCacheManager(BaseModel):
    """Manage a two-level in-memory cache."""

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

    def get(self, key: str) -> Optional[Any]:
        if key in self._level1:
            return self._level1[key]
        return self._level2.get(key)

    def set(self, key: str, value: Any, *, level: int = 1) -> None:
        if level == 1:
            self._level1[key] = value
        else:
            self._level2[key] = value

    def clear(self) -> None:
        self._level1.clear()
        self._level2.clear()

    async def warm(self, keys: list[str], loader: Callable[[str], Any]) -> None:
        """Pre-populate all cache tiers for the specified *keys*.

        The *loader* callable is used to retrieve the value for each key. It can
        be either a synchronous function or an async coroutine. Values are stored
        in both cache levels.
        """

        async def _populate(key: str) -> None:
            if inspect.iscoroutinefunction(loader):
                value = await loader(key)
            else:
                value = await asyncio.to_thread(loader, key)
            self.set(key, value, level=1)
            self.set(key, value, level=2)

        await asyncio.gather(*(_populate(k) for k in keys))


__all__ = ["HierarchicalCacheManager"]
