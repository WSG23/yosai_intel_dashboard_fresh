from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import asyncpg
import redis.asyncio as aioredis

from yosai_intel_dashboard.models.ml import ModelRegistry
from yosai_intel_dashboard.src.infrastructure.config.config_loader import (
    ServiceSettings,
)
from yosai_intel_dashboard.src.services.common.analytics_utils import (
    preload_active_models,
)
from yosai_intel_dashboard.src.services.common.async_db import close_pool


class AnalyticsService:
    """Manage shared resources for the analytics microservice."""

    def __init__(
        self,
        redis: aioredis.Redis,
        pool: asyncpg.pool.Pool,
        model_registry: ModelRegistry,
        cfg: ServiceSettings,
    ) -> None:
        self.redis = redis
        self.pool = pool
        self.model_registry = model_registry
        self.cache_ttl = cfg.cache_ttl
        self.model_dir = Path(cfg.model_dir)
        self.models: dict[str, Any] = {}

    async def close(self) -> None:
        await close_pool()
        if self.redis is not None:
            await self.redis.close()

    def preload_active_models(self) -> None:
        """Load active models into memory from the registry."""
        preload_active_models(self)


async def get_analytics_service(request: Any) -> AnalyticsService:
    """Fetch the :class:`AnalyticsService` instance from a request object."""

    return cast(AnalyticsService, request.app.state.analytics_service)
