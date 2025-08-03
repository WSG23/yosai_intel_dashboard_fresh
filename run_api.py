import asyncio
import logging
import os

from api.adapter import create_api_app
from yosai_intel_dashboard.src.core.cache_warmer import IntelligentCacheWarmer
from yosai_intel_dashboard.src.core.di.bootstrap import bootstrap_container
from yosai_intel_dashboard.src.core.env_validation import validate_required_env
from yosai_intel_dashboard.src.infrastructure.config import get_cache_config
from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_required_env()
    container = bootstrap_container()

    cache_cfg = get_cache_config()
    cache_manager = container.get("cache_manager")

    def _load(key: str) -> None:
        return None

    # Warm cache based on stored usage statistics
    usage_path = getattr(cache_cfg, "usage_stats_path", os.getenv("CACHE_USAGE_FILE"))
    if usage_path and hasattr(cache_manager, "get"):
        warmer = IntelligentCacheWarmer(cache_manager, _load)
        asyncio.run(warmer.warm_from_file(usage_path))

    warm_keys = getattr(cache_cfg, "warm_keys", [])
    if warm_keys and hasattr(cache_manager, "warm"):
        asyncio.run(cache_manager.warm(warm_keys, _load))

    app = create_api_app()
    app.state.container = container

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
