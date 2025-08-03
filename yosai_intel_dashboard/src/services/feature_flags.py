from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List

import aiofiles
import aiohttp

from monitoring import cache_refreshes, flag_evaluations, flag_fallbacks

logger = logging.getLogger(__name__)


class FeatureFlagManager:
    """Watch a JSON file or HTTP endpoint for feature flag updates."""

    def __init__(self, source: str | None = None, poll_interval: float = 5.0) -> None:
        self.source = source or os.getenv("FEATURE_FLAG_SOURCE", "feature_flags.json")
        self.poll_interval = poll_interval
        self._flags: Dict[str, bool] = {}
        self._callbacks: List[Callable[[Dict[str, bool]], Any]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_mtime: float | None = None
        asyncio.run(self.load_flags())

    async def load_flags_async(self) -> None:
        """Asynchronously load flags from the configured source."""

        data: Dict[str, Any] = {}
        if self.source.startswith("http://") or self.source.startswith("https://"):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(self.source, timeout=2) as resp:

                        resp.raise_for_status()
                        data = await resp.json()
            except Exception as exc:  # pragma: no cover - network failures
                logger.warning("Failed to fetch flags from %s: %s", self.source, exc)
                return
        else:
            path = Path(self.source)
            if not path.is_file():
                return
            mtime = path.stat().st_mtime
            if self._last_mtime and mtime == self._last_mtime:
                return
            self._last_mtime = mtime
            try:
                async with aiofiles.open(path) as fh:
                    content = await fh.read()
                    data = json.loads(content)
            except Exception as exc:  # pragma: no cover - bad file
                logger.warning("Failed to read %s: %s", path, exc)
                return

        if isinstance(data, dict):
            new_flags = {k: bool(v) for k, v in data.items()}
            if new_flags != self._flags:
                self._flags = new_flags
                cache_refreshes.inc()
                for cb in list(self._callbacks):
                    try:
                        cb(self._flags.copy())
                    except Exception as exc:  # pragma: no cover - callback errors
                        logger.warning("Feature flag callback failed: %s", exc)

    def load_flags(self) -> None:
        """Synchronous wrapper for :meth:`load_flags_async`."""
        asyncio.run(self.load_flags_async())

    def start(self) -> None:
        """Start background watcher for flag changes."""
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()

    def stop(self) -> None:
        """Stop the background watcher."""
        if self._thread:
            self._stop.set()
            self._thread.join()

    def _watch(self) -> None:
        while not self._stop.is_set():
            asyncio.run(self.load_flags_async())
            if self._stop.wait(self.poll_interval):
                break

    def is_enabled(self, name: str, default: bool = False) -> bool:
        """Return True if *name* flag is enabled."""
        flag_evaluations.inc()
        if name not in self._flags:
            flag_fallbacks.inc()
        return self._flags.get(name, default)

    def register_callback(self, cb: Callable[[Dict[str, bool]], Any]) -> None:
        """Register *cb* to be called when flags change."""
        self._callbacks.append(cb)

    def get_all(self) -> Dict[str, bool]:
        return self._flags.copy()


# Global feature flag manager
feature_flags = FeatureFlagManager()
