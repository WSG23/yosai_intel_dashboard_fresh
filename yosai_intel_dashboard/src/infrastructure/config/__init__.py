"""
Central export point for configuration helpers.

- If a real get_cache_config() exists in a submodule (e.g., .cache), re-export it.
- Otherwise, provide a minimal, environment-driven fallback so the API can boot.
"""

from __future__ import annotations

import os
from typing import Any, Dict

# Try to import the real implementation if present.
try:
    from .cache import get_cache_config as _real_get_cache_config  # type: ignore[attr-defined]
except Exception:
    _real_get_cache_config = None  # type: ignore[assignment]

def get_cache_config() -> Dict[str, Any]:
    """
    Return cache configuration as a dict. Prefer project-defined implementation;
    otherwise fall back to env vars so the container can start.
    """
    if _real_get_cache_config is not None:
        return _real_get_cache_config()

    # Fallback: Redis if REDIS_URL set; otherwise in-memory
    backend = os.getenv("CACHE_BACKEND")
    if not backend:
        backend = "redis" if os.getenv("REDIS_URL") else "memory"

    return {
        "backend": backend,
        "url": os.getenv("REDIS_URL", "redis://redis:6379/0"),
        "ttl": int(os.getenv("CACHE_TTL", "300")),
    }

__all__ = ["get_cache_config"]
