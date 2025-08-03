import asyncio
import logging
import os
import importlib.util
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Callable


# Dynamically load the redis store located beside this module.  If the
# dependency is missing (e.g. during tests), fall back to a no-op store.
class InMemoryFeatureFlagStore:  # type: ignore
    def __init__(self, *_, **__) -> None:
        self._flags: Dict[str, bool] = {}

    def start(self) -> None:  # pragma: no cover - no-op
        pass

    def stop(self) -> None:  # pragma: no cover - no-op
        pass

    def get_flag(self, name: str, default: bool = False) -> bool:
        return self._flags.get(name, default)

    def set_flag(self, name: str, value: bool) -> None:
        self._flags[name] = value

    def get_all(self) -> Dict[str, bool]:
        return dict(self._flags)

try:  # pragma: no cover - optional dependency
    _store_path = Path(__file__).with_name("feature_flags") / "redis_store.py"
    _spec = importlib.util.spec_from_file_location("_ff_redis_store", _store_path)
    redis_store = importlib.util.module_from_spec(_spec)
    _spec.loader.exec_module(redis_store)  # type: ignore[arg-type]
    RedisFeatureFlagStore = redis_store.RedisFeatureFlagStore
except Exception:  # pragma: no cover - simplified fallback
    RedisFeatureFlagStore = InMemoryFeatureFlagStore

from ..repository import (
    AsyncFileFeatureFlagCacheRepository,
    FeatureFlagCacheRepository,
)


logger = logging.getLogger(__name__)


def get_evaluation_context() -> Dict[str, Any]:
    """Return context for flag evaluation including user roles.

    The current ``User`` from :mod:`core.auth` may expose a ``roles``
    attribute.  These roles are included so that flag rules can target
    specific groups.
    """

    roles: List[str] = []
    user_id: Optional[str] = None
    try:  # pragma: no cover - no request active during some tests
        from flask_login import current_user  # type: ignore

        if getattr(current_user, "is_authenticated", False):
            user_id = getattr(current_user, "id", None)
            roles = getattr(current_user, "roles", []) or []
    except Exception:  # pragma: no cover - best effort
        pass
    return {"user_id": user_id, "roles": roles}


class FeatureFlagManager:
    """Feature flag manager backed by Redis with a pluggable cache."""

    def __init__(
        self,
        redis_url: str | None = None,
        cache_repo: FeatureFlagCacheRepository | None = None,
    ) -> None:
        redis_url = redis_url or os.getenv(
            "FEATURE_FLAG_REDIS_URL", "redis://localhost:6379/0"
        )
        try:
            self._store = RedisFeatureFlagStore(redis_url=redis_url)
        except Exception:  # pragma: no cover - redis optional
            self._store = InMemoryFeatureFlagStore()
        # expose the cache for tests that monkeypatch _flags
        self._flags = self._store._flags
        self._definitions: Dict[str, Dict[str, Any]] = {}
        self._callbacks: Set[Callable[[Dict[str, bool]], None]] = set()
        self._cache_repo = cache_repo or AsyncFileFeatureFlagCacheRepository(
            Path("feature_flags_cache.json")
        )
        self._load_cache()


    # ------------------------------------------------------------------
    def start(self) -> None:
        """Start the background Pub/Sub listener."""
        self._store.start()

    # ------------------------------------------------------------------
    def stop(self) -> None:
        """Stop the background Pub/Sub listener."""
        self._store.stop()

    def is_enabled(self, name: str, default: bool = False) -> bool:
        return self._store.get_flag(name, default)

    def set_flag(self, name: str, value: bool) -> None:
        self._store.set_flag(name, value)


    # ------------------------------------------------------------------
    def get_all(self) -> Dict[str, bool]:
        return self._store.get_all()

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
    async def _load_cache_async(self) -> None:
        cached = await self._cache_repo.read()
        if cached:
            self._flags = cached
            try:
                self._store._flags = dict(cached)  # type: ignore[attr-defined]
            except Exception:
                pass
            for name, val in self._flags.items():
                self._definitions.setdefault(name, {"fallback": False})[
                    "enabled"
                ] = val

    def _load_cache(self) -> None:
        """Synchronous wrapper around :meth:`_load_cache_async`."""
        asyncio.run(self._load_cache_async())

    # ------------------------------------------------------------------
    async def _save_cache(self) -> None:
        await self._cache_repo.write(self._flags)


__all__ = ["FeatureFlagManager", "get_evaluation_context"]
