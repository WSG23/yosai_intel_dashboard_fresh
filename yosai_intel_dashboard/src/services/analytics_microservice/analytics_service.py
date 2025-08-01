from __future__ import annotations

from pathlib import Path
from typing import Any

import asyncpg
import redis.asyncio as aioredis

from yosai_intel_dashboard.src.services.common.async_db import close_pool
from yosai_intel_dashboard.models.ml import ModelRegistry


class AnalyticsService:
    """Manage shared resources for the analytics microservice."""

    def __init__(
        self,
        redis: aioredis.Redis,
        pool: asyncpg.pool.Pool,
        model_registry: ModelRegistry,
        *,
        cache_ttl: int = 300,
        model_dir: Path | None = None,
    ) -> None:
        self.redis = redis
        self.pool = pool
        self.model_registry = model_registry
        self.cache_ttl = cache_ttl
        self.model_dir = model_dir or Path("model_store")
        self.models: dict[str, Any] = {}

    async def close(self) -> None:
        await close_pool()
        if self.redis is not None:
            await self.redis.close()

    def preload_active_models(self) -> None:
        """Load active models into memory from the registry."""
        self.models = {}
        registry = self.model_registry
        try:
            records = registry.list_models()
        except Exception:  # pragma: no cover - registry unavailable
            return
        names = {r.name for r in records}
        for name in names:
            record = registry.get_model(name, active_only=True)
            if record is None:
                continue
            local_dir = self.model_dir / name / record.version
            local_dir.mkdir(parents=True, exist_ok=True)
            filename = record.storage_uri.split("/")[-1]
            local_path = local_dir / filename
            if not local_path.exists():
                try:
                    registry.download_artifact(record.storage_uri, str(local_path))
                except Exception:  # pragma: no cover - best effort
                    continue
            try:
                import joblib

                model_obj = joblib.load(local_path)
                self.models[name] = model_obj
            except Exception:  # pragma: no cover - invalid model
                continue


async def get_analytics_service(request) -> AnalyticsService:
    return request.app.state.analytics_service
