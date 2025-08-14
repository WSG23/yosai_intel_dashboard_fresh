from __future__ import annotations

import httpx

from services.resilience.circuit_breaker import CircuitBreaker


class BreakerClient:
    """HTTPX client wrapped with a circuit breaker."""

    def __init__(
        self,
        *,
        timeout: float = 5.0,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        name: str = "httpx",
    ) -> None:
        self._client = httpx.AsyncClient(timeout=timeout)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold, recovery_timeout, name=name
        )

    async def request(self, method: str, url: str, **kwargs):
        async with self.circuit_breaker:
            response = await self._client.request(method, url, **kwargs)
        response.raise_for_status()
        return response

    async def aclose(self) -> None:
        await self._client.aclose()

__all__ = ["BreakerClient"]

