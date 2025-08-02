from __future__ import annotations

import logging

from api.adapter import create_api_app
from core.di.bootstrap import bootstrap_container
from core.env_validation import validate_required_env
from yosai_intel_dashboard.src.infrastructure.config import get_cache_config
from yosai_intel_dashboard.src.infrastructure.config.constants import API_PORT

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    validate_required_env()
    container = bootstrap_container()

    cache_cfg = get_cache_config()
    warm_keys = getattr(cache_cfg, "warm_keys", [])
    if warm_keys:
        cache_manager = container.get("cache_manager")
        if hasattr(cache_manager, "warm"):

            def _load(key: str) -> None:
                return None

            import asyncio

            asyncio.run(cache_manager.warm(warm_keys, _load))

    app = create_api_app()
    app.state.container = container

    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=API_PORT)
