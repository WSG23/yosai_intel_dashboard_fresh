from __future__ import annotations

import logging
import ssl
from typing import Any, MutableMapping

import aiohttp
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from services.resilience.circuit_breaker import CircuitBreaker, CircuitBreakerOpen

from .protocols import ServiceClient


class RestClient:
    """Asynchronous HTTP client with circuit breaker and retries."""

    log = logging.getLogger(__name__)

    def __init__(
        self,
        base_url: str,
        *,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        retries: int = 3,
        timeout: float = 5.0,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.circuit_breaker = CircuitBreaker(
            failure_threshold, recovery_timeout, name=base_url
        )
        self.retries = retries
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._ssl = self._create_ssl_context(mtls_cert, mtls_key, verify_ssl)

    # ------------------------------------------------------------------
    def _create_ssl_context(
        self, cert: str | None, key: str | None, verify_ssl: bool
    ) -> ssl.SSLContext | bool | None:
        if cert and key:
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ctx.load_cert_chain(certfile=cert, keyfile=key)
            if not verify_ssl:
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
            return ctx
        if not verify_ssl:
            return False
        return None

    # ------------------------------------------------------------------
    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send an HTTP request with retries and tracing."""

        url = self.base_url + path
        headers: MutableMapping[str, str] = kwargs.pop("headers", {}) or {}
        propagate_context(headers)
        kwargs["headers"] = headers

        async def _do_request() -> Any:
            async with self.circuit_breaker:
                async with aiohttp.ClientSession() as session:
                    async with session.request(
                        method,
                        url,
                        timeout=self.timeout,
                        ssl=self._ssl,
                        **kwargs,
                    ) as resp:
                        self.log.info("%s %s -> %s", method, url, resp.status)
                        resp.raise_for_status()
                        ctype = resp.headers.get("Content-Type", "")
                        if "application/json" in ctype:
                            return await resp.json()
                        return await resp.text()


def create_service_client(service_name: str) -> ServiceClient:
    """Create a service client resolving *service_name* URL from env vars."""
    env = f"{service_name.upper()}_SERVICE_URL"
    base_url = os.getenv(env, f"http://{service_name}")
    return AsyncRestClient(base_url)


__all__ = [
    "AsyncRestClient",
    "RetryPolicy",
    "create_service_client",
    "CircuitBreakerOpen",
]
