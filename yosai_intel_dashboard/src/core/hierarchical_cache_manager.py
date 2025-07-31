from __future__ import annotations

"""Simple hierarchical cache with two levels."""

import logging
from typing import Any, Dict, Optional

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


__all__ = ["HierarchicalCacheManager"]
