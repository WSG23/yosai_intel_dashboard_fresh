from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from pathlib import Path
from typing import Any, Callable, Dict, List, Set

import aiofiles
import aiohttp

try:  # pragma: no cover - optional dependency
    import redis.asyncio as redis
except Exception:  # pragma: no cover - fallback if redis not installed
    redis = None  # type: ignore


logger = logging.getLogger(__name__)


# Default flag definitions with fallbacks. Additional flags may be provided at
# runtime from Redis or a JSON source. Each definition contains a "fallback"
# value and optional list of dependencies under "requires".
FLAG_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "use_kafka_events": {"fallback": False, "requires": []},
    "use_timescaledb": {"fallback": False, "requires": []},
    "use_analytics_microservice": {"fallback": False, "requires": []},
}


class FeatureFlagManager:
    """Watch a JSON file, HTTP endpoint or Redis for feature flag updates."""

    def __init__(
        self,
        source: str | None = None,
        poll_interval: float = 5.0,
        redis_url: str | None = None,
        cache_file: str | Path | None = None,
    ) -> None:
        self.source = source or os.getenv("FEATURE_FLAG_SOURCE", "feature_flags.json")
        self.poll_interval = poll_interval
        self.redis_url = redis_url or os.getenv("FEATURE_FLAG_REDIS_URL")
        self.redis_key = os.getenv("FEATURE_FLAG_REDIS_KEY", "feature_flags")
        self.cache_file = Path(
            cache_file or os.getenv("FEATURE_FLAG_CACHE", "feature_flags_cache.json")
        )
        # ``_definitions`` holds flag metadata including fallbacks and dependencies
        self._definitions: Dict[str, Dict[str, Any]] = json.loads(
            json.dumps(FLAG_DEFINITIONS)
        )
        # ``_flags`` holds the last evaluated values for quick lookup
        self._flags: Dict[str, bool] = {}
        self._callbacks: List[Callable[[Dict[str, bool]], Any]] = []
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_mtime: float | None = None
        self._fallback_mode = False
        self._warned_fallback = False
        self._redis: redis.Redis | None = None

        # Load cached flags before attempting any remote fetches
        self._load_cache()
        self._recompute_flags()
        self.load_flags()

    # ------------------------------------------------------------------
    async def load_flags_async(self) -> None:
        """Asynchronously load flags from Redis, HTTP or file sources."""

        data: Dict[str, Any] = {}
        if self.redis_url and redis is not None:
            try:
                if self._redis is None:
                    self._redis = redis.from_url(self.redis_url, decode_responses=True)
                raw = await self._redis.get(self.redis_key)
                data = json.loads(raw) if raw else {}
            except Exception as exc:  # pragma: no cover - network failures
                self._fallback_mode = True
                logger.warning("Failed to fetch flags from Redis: %s", exc)
                return
        elif self.source and (
            self.source.startswith("http://") or self.source.startswith("https://")
        ):
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
            for name, value in data.items():
                definition = self._definitions.setdefault(name, {"fallback": False})
                if isinstance(value, dict):
                    definition["enabled"] = bool(
                        value.get("enabled", value.get("value", False))
                    )
                    if "fallback" in value:
                        definition["fallback"] = bool(value["fallback"])
                    if "requires" in value:
                        definition["requires"] = list(value["requires"])
                else:
                    definition["enabled"] = bool(value)
            self._recompute_flags()
            await self._save_cache()
            self._fallback_mode = False
            self._warned_fallback = False

    # ------------------------------------------------------------------
    def load_flags(self) -> None:
        """Synchronous wrapper for :meth:`load_flags_async`."""
        asyncio.run(self.load_flags_async())

    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start background watcher for flag changes."""
        if self._thread and self._thread.is_alive():
            return

        self._stop.clear()
        self._thread = threading.Thread(target=self._watch, daemon=True)
        self._thread.start()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the background watcher."""
        if self._thread:
            self._stop.set()
            self._thread.join()

    # ------------------------------------------------------------------
    def _watch(self) -> None:
        while not self._stop.is_set():
            asyncio.run(self.load_flags_async())
            if self._stop.wait(self.poll_interval):
                break

    # ------------------------------------------------------------------
    def is_enabled(self, name: str, default: bool = False) -> bool:
        """Return True if *name* flag is enabled."""

        if self._fallback_mode and not self._warned_fallback:
            logger.warning("FeatureFlagManager operating in fallback mode")
            self._warned_fallback = True

        if name in self._flags:
            return self._flags[name]

        definition = self._definitions.get(name)
        if definition is not None:
            return bool(definition.get("fallback", default))
        return default

    # ------------------------------------------------------------------
    def register_callback(self, cb: Callable[[Dict[str, bool]], Any]) -> None:
        """Register *cb* to be called when flags change."""
        self._callbacks.append(cb)

    # ------------------------------------------------------------------
    def get_all(self) -> Dict[str, bool]:
        return self._flags.copy()

    # ------------------------------------------------------------------
    def _resolve(self, name: str, seen: Set[str]) -> bool:
        if name in seen:
            raise RuntimeError("circular dependency detected")
        seen.add(name)
        definition = self._definitions.get(name, {})
        enabled = bool(definition.get("enabled", definition.get("fallback", False)))
        requires = definition.get("requires", [])
        for dep in requires:
            if dep not in self._definitions:
                raise KeyError(f"missing dependency {dep}")
            if not self._resolve(dep, seen):
                return bool(definition.get("fallback", False))
        return enabled

    # ------------------------------------------------------------------
    def _recompute_flags(self) -> None:
        new_flags: Dict[str, bool] = {}
        for name in self._definitions:
            try:
                new_flags[name] = self._resolve(name, set())
            except Exception as exc:  # pragma: no cover - defensive
                fallback = bool(self._definitions[name].get("fallback", False))
                logger.warning("Failed to evaluate feature flag %s: %s", name, exc)
                new_flags[name] = fallback

        if new_flags != self._flags:
            self._flags = new_flags
            for cb in list(self._callbacks):
                try:
                    cb(self._flags.copy())
                except Exception as exc:  # pragma: no cover - callback errors
                    logger.warning("Feature flag callback failed: %s", exc)

    # ------------------------------------------------------------------
    def _load_cache(self) -> None:
        try:
            if self.cache_file.is_file():
                content = self.cache_file.read_text()
                cached = json.loads(content)
                self._flags = {k: bool(v) for k, v in cached.items()}
                for name, val in self._flags.items():
                    self._definitions.setdefault(name, {"fallback": False})[
                        "enabled"
                    ] = val
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to load feature flag cache: %s", exc)

    # ------------------------------------------------------------------
    async def _save_cache(self) -> None:
        try:
            async with aiofiles.open(self.cache_file, "w") as fh:
                await fh.write(json.dumps(self._flags))
        except Exception as exc:  # pragma: no cover - defensive
            logger.warning("Failed to persist feature flag cache: %s", exc)


# Global feature flag manager
feature_flags = FeatureFlagManager(
    redis_url=os.getenv("FEATURE_FLAG_REDIS_URL"),
)
