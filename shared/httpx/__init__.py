"""HTTPX client instrumented with a circuit breaker."""

from __future__ import annotations

from typing import Awaitable, Callable, Optional

import httpx

from services.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpen


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

    async def request(
        self,
        method: str,
        url: str,
        *,
        fallback: Optional[Callable[[], Awaitable[httpx.Response]]] = None,
        **kwargs,
    ) -> httpx.Response:
        """Perform an HTTP request guarded by the circuit breaker.

        Parameters
        ----------
        method, url, **kwargs:
            Passed directly to ``httpx.AsyncClient.request``.
        fallback:
            Optional coroutine invoked when the circuit is open. If provided,
            the HTTP request is skipped and the fallback response returned.
        """
        try:
            async with self.circuit_breaker:
                response = await self._client.request(method, url, **kwargs)
        except CircuitBreakerOpen:
            if fallback is not None:
                return await fallback()
            raise
        response.raise_for_status()
        return response

    async def aclose(self) -> None:
        await self._client.aclose()


__all__ = ["BreakerClient"]

