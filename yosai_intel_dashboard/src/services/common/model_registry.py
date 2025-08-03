import asyncio
import logging
import os
import warnings
from typing import Optional

import aiohttp

from yosai_intel_dashboard.src.error_handling import ErrorCategory, ErrorHandler
from yosai_intel_dashboard.src.services.resilience.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Lightweight client for querying the active AI model version."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (
            base_url or os.getenv("MODEL_REGISTRY_URL", "http://localhost:8080")
        ).rstrip("/")
        self._session: aiohttp.ClientSession | None = None
        self._cache: dict[str, str] = {}
        self._lock = asyncio.Lock()
        self._breaker = CircuitBreaker(3, 30, "model_registry")
        self._retries = 3
        self._error_handler = ErrorHandler()

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_active_version_async(
        self, model_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Return the active version for *model_name* or a fallback."""
        async with self._lock:
            cached = self._cache.get(model_name)

        for attempt in range(self._retries):
            try:
                async with self._breaker:
                    session = await self._get_session()
                    async with session.get(
                        f"{self.base_url}/models/{model_name}/active",
                        timeout=aiohttp.ClientTimeout(total=2),
                    ) as resp:
                        resp.raise_for_status()
                        data = await resp.json()
                version = data.get("version", default)
                if version is not None:
                    async with self._lock:
                        self._cache[model_name] = version
                return version
            except CircuitBreakerOpen as exc:
                self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
                return cached if cached is not None else default
            except Exception as exc:  # pragma: no cover - network failures
                self._error_handler.handle(exc, ErrorCategory.UNAVAILABLE)
                if attempt + 1 == self._retries:
                    return cached if cached is not None else default
                await asyncio.sleep(0.1 * (attempt + 1))

        return cached if cached is not None else default

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    def get_active_version(
        self, model_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Synchronous wrapper for :meth:`get_active_version_async`."""
        warnings.warn(
            "get_active_version is deprecated, use get_active_version_async",
            DeprecationWarning,
            stacklevel=2,
        )
        return asyncio.run(self.get_active_version_async(model_name, default))


__all__ = ["ModelRegistry"]
