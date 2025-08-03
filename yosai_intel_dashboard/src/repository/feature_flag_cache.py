"""Feature flag cache repository abstractions."""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Dict, Protocol

import aiofiles

logger = logging.getLogger(__name__)


class FeatureFlagCacheRepository(Protocol):
    """Persist and retrieve cached feature flag data."""

    async def read(self) -> Dict[str, bool]:
        """Return cached flag mappings."""
        ...

    async def write(self, flags: Dict[str, bool]) -> None:
        """Persist flag mapping to the cache."""
        ...


class AsyncFileFeatureFlagCacheRepository:
    """Store feature flags as JSON on the local filesystem."""

    def __init__(self, path: Path) -> None:
        self._path = path

    async def read(self) -> Dict[str, bool]:
        try:
            if await asyncio.to_thread(self._path.is_file):
                async with aiofiles.open(self._path, "r") as fh:
                    data = json.loads(await fh.read())
                return {k: bool(v) for k, v in data.items()}
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load feature flag cache: %s", exc)
        return {}

    async def write(self, flags: Dict[str, bool]) -> None:
        try:
            async with aiofiles.open(self._path, "w") as fh:
                await fh.write(json.dumps(flags))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to persist feature flag cache: %s", exc)
