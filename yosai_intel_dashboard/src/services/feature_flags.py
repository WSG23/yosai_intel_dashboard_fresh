import logging
import os
import importlib.util
from pathlib import Path
from typing import Dict

# Dynamically load the redis store located beside this module
_store_path = Path(__file__).with_name("feature_flags") / "redis_store.py"
_spec = importlib.util.spec_from_file_location("_ff_redis_store", _store_path)
redis_store = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(redis_store)  # type: ignore[arg-type]
RedisFeatureFlagStore = redis_store.RedisFeatureFlagStore

logger = logging.getLogger(__name__)


class FeatureFlagManager:
    """Feature flag manager backed by Redis with a local cache."""

    def __init__(self, redis_url: str | None = None) -> None:
        redis_url = redis_url or os.getenv("FEATURE_FLAG_REDIS_URL", "redis://localhost:6379/0")
        self._store = RedisFeatureFlagStore(redis_url=redis_url)
        # expose the cache for tests that monkeypatch _flags
        self._flags = self._store._flags

    def start(self) -> None:
        """Start the background Pub/Sub listener."""
        self._store.start()

    def stop(self) -> None:
        """Stop the background Pub/Sub listener."""
        self._store.stop()

    def is_enabled(self, name: str, default: bool = False) -> bool:
        return self._store.get_flag(name, default)

    def set_flag(self, name: str, value: bool) -> None:
        self._store.set_flag(name, value)

    def get_all(self) -> Dict[str, bool]:
        return self._store.get_all()


# Global feature flag manager
feature_flags = FeatureFlagManager()
