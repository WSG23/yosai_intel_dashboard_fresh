import asyncio
import logging
import os
import warnings
from typing import Optional

import aiohttp

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Lightweight client for querying the active AI model version."""

    def __init__(self, base_url: Optional[str] = None) -> None:
        self.base_url = (
            base_url or os.getenv("MODEL_REGISTRY_URL", "http://localhost:8080")
        ).rstrip("/")
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session

    async def get_active_version_async(
        self, model_name: str, default: Optional[str] = None
    ) -> Optional[str]:
        """Return the active version for *model_name* or *default* if lookup fails."""
        try:
            session = await self._get_session()
            async with session.get(
                f"{self.base_url}/models/{model_name}/active",
                timeout=aiohttp.ClientTimeout(total=2),
            ) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("version", default)
        except Exception as exc:  # pragma: no cover - network failures
            logger.warning("model registry lookup failed for %s: %s", model_name, exc)
            return default

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
