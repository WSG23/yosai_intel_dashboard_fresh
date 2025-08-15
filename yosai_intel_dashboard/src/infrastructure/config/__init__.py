"""
Central export point for configuration helpers.

- If a real get_cache_config() exists in a submodule (e.g., .cache), re-export it.
- Otherwise, provide a minimal, attribute-accessible fallback so the API can boot.
"""

from __future__ import annotations

import os
from typing import Any, Dict

# Try to import the real implementation if present.
try:
    from .cache import get_cache_config as _real_get_cache_config  # type: ignore[attr-defined]
except Exception:
    _real_get_cache_config = None  # type: ignore[assignment]


class CacheConfig(dict):
    """Dict subclass with attribute access for backwards compatibility."""
    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(name)


def get_cache_config() -> CacheConfig:
    """
    Return cache configuration as a dict-like object with attribute access.
    Prefer project-defined implementation; otherwise fall back to env vars.
    """
    if _real_get_cache_config is not None:
        cfg = _real_get_cache_config()
        # Wrap in CacheConfig if it's a dict
        if isinstance(cfg, dict) and not isinstance(cfg, CacheConfig):
            return CacheConfig(cfg)
        return cfg  # Already object-like

    backend = os.getenv("CACHE_BACKEND") or ("redis" if os.getenv("REDIS_URL") else "memory")

    return CacheConfig({
        "backend": backend,
        "url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        "ttl": int(os.getenv("CACHE_TTL", "300")),
    })


__all__ = ["get_cache_config"]
