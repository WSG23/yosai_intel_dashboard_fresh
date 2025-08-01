from __future__ import annotations

import logging
import os
import ssl
from typing import Any, MutableMapping

import aiohttp
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)
from tracing import propagate_context


class K8sResolver:
    """Resolve service URLs inside a Kubernetes cluster."""

    def __init__(self, namespace: str | None = None, scheme: str = "http") -> None:
        self.namespace = namespace or os.getenv("K8S_NAMESPACE", "default")
        self.scheme = scheme

    def resolve(self, name: str) -> str:
        return f"{self.scheme}://{name}.{self.namespace}.svc.cluster.local"


class ServiceClient:
    """Asynchronous HTTP client for internal services with resiliency."""

    log = logging.getLogger(__name__)

    def __init__(
        self,
        service_name: str,
        *,
        resolver: K8sResolver | None = None,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        retries: int = 3,
        timeout: float = 5.0,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ssl: bool = True,
    ) -> None:
        self.service_name = service_name
        self.resolver = resolver or K8sResolver()
        self.base_url = self.resolver.resolve(service_name)
        self.circuit_breaker = CircuitBreaker(
            failure_threshold, recovery_timeout, name=service_name
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

        async for attempt in AsyncRetrying(
            reraise=True,
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(multiplier=0.5, min=0.5, max=5),
            retry=retry_if_exception_type(aiohttp.ClientError),
        ):
            with attempt:
                return await _do_request()


__all__ = ["K8sResolver", "ServiceClient", "CircuitBreakerOpen"]
