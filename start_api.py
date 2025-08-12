#!/usr/bin/env python3

from __future__ import annotations

"""Unified entry point for starting the Yosai Intel Dashboard API.

This script validates required environment variables, warms the cache based on
usage statistics and configured warm keys, then starts the FastAPI server.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))


def main() -> None:
    """Warm the cache and start the API server."""
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

    def _load(key: str) -> None:
        return None

    usage_path = getattr(cache_cfg, "usage_stats_path", os.getenv("CACHE_USAGE_FILE"))
    if usage_path and hasattr(cache_manager, "get"):
        warmer = IntelligentCacheWarmer(cache_manager, _load)
        asyncio.run(warmer.warm_from_file(usage_path))

    warm_keys = getattr(cache_cfg, "warm_keys", [])
    if warm_keys and hasattr(cache_manager, "warm"):
        asyncio.run(cache_manager.warm(warm_keys, _load))

    app = create_api_app()
    app.state.container = container

    # Ensure a basic health endpoint is available
    if not any(getattr(route, "path", None) == "/health" for route in app.router.routes):
        @app.get("/health")
        async def _health() -> dict[str, str]:
            return {"status": "ok"}

    logger.info("\n🚀 Starting Yosai Intel Dashboard API...")
    logger.info(f"   Available at: http://localhost:{API_PORT}")
    logger.info(f"   Health check: http://localhost:{API_PORT}/health")

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
