from __future__ import annotations

import os
import httpx

from services.resilience.circuit_breaker import CircuitBreaker


class BreakerClient:
    """HTTPX client wrapped with a circuit breaker.

    The client reads standard TLS environment variables (``TLS_CERT_FILE``,
    ``TLS_KEY_FILE`` and ``TLS_CA_FILE``) and configures mutual TLS for
    outbound requests when provided.
    """

    def __init__(
        self,
        *,
        timeout: float = 5.0,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        name: str = "httpx",
    ) -> None:
        tls_cert = os.getenv("TLS_CERT_FILE")
        tls_key = os.getenv("TLS_KEY_FILE")
        tls_ca = os.getenv("TLS_CA_FILE")
        verify = tls_ca or True
        cert = (tls_cert, tls_key) if tls_cert and tls_key else None
        self._client = httpx.AsyncClient(timeout=timeout, verify=verify, cert=cert)
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

