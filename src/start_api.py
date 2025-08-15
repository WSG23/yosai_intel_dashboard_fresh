#!/usr/bin/env python3

"""Unified entry point for starting the Yosai Intel Dashboard API.

This script validates required environment variables, warms the cache based on
usage statistics and configured warm keys, then starts the FastAPI server.
"""

from __future__ import annotations

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, Type

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


def _noop_loader(key: str) -> None:
    """Default cache loader used during warmup.

    Args:
        key: Cache key being loaded.

    Returns:
        None
    """
    return None


def _warm_cache(
    cache_manager: Any,
    cache_cfg: Any,
    warmer_cls: Type[Any],
    load_fn: Callable[[str], None],
) -> None:
    """Warm cache from usage stats and configured warm keys.

    Args:
        cache_manager: Cache manager instance used for warmup.
        cache_cfg: Cache configuration object.
        warmer_cls: Class implementing the warmup strategy.
        load_fn: Function used to populate a missing cache entry.

    Returns:
        None
    """
    usage_path = getattr(cache_cfg, "usage_stats_path", os.getenv("CACHE_USAGE_FILE"))
    if usage_path and hasattr(cache_manager, "get"):
        warmer = warmer_cls(cache_manager, load_fn)
        asyncio.run(warmer.warm_from_file(usage_path))

    warm_keys = getattr(cache_cfg, "warm_keys", [])
    if warm_keys and hasattr(cache_manager, "warm"):
        asyncio.run(cache_manager.warm(warm_keys, load_fn))


def _ensure_health_endpoint(app: Any) -> None:
    """Add a `/health` route to ``app`` if missing.

    Args:
        app: FastAPI application instance to modify.

    Returns:
        None
    """
    if any(getattr(r, "path", "") == "/health" for r in app.routes):
        return

    @app.get("/health")  # type: ignore[misc]
    async def _health() -> dict[str, str]:
        return {"status": "ok"}


def main() -> None:
    """Warm the cache and start the API server.

    Returns:
        None
    """
    try:
        import uvicorn

        from yosai_intel_dashboard.src.adapters.api.adapter import create_api_app
        from yosai_intel_dashboard.src.core.cache_warmer import IntelligentCacheWarmer
        from yosai_intel_dashboard.src.core.di.bootstrap import bootstrap_container
        from yosai_intel_dashboard.src.core.env_validation import validate_required_env
        from yosai_intel_dashboard.src.infrastructure.config import get_cache_config
        from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT
    except ModuleNotFoundError as exc:
        missing_pkg = getattr(exc, "name", None) or str(exc)
        logger.error(
            "Missing required dependency '%s'. "
            "Install it with 'pip install -r requirements.txt' and try again.",
            missing_pkg,
        )
        raise SystemExit(1)
    except ImportError as exc:
        logger.error(
            "Failed to import dependencies (possible circular import): %s", exc
        )
        raise SystemExit(1)

    validate_required_env()
    container = bootstrap_container()

    cache_cfg = get_cache_config()
    cache_manager = container.get("cache_manager")

    _warm_cache(cache_manager, cache_cfg, IntelligentCacheWarmer, _noop_loader)

    app = create_api_app()
    app.state.container = container

    _ensure_health_endpoint(app)

    logger.info("\n🚀 Starting Yosai Intel Dashboard API...")
    logger.info(f"   Available at: http://localhost:{API_PORT}")
    logger.info(f"   Health check: http://localhost:{API_PORT}/health")

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
