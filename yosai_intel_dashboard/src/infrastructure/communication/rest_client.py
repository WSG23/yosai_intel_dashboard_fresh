from __future__ import annotations

import asyncio
import contextlib
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

from tracing import propagate_context
from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)
from yosai_intel_dashboard.src.services.resilience.recovery import monitor_dependency


class RestClient:
    """Asynchronous HTTP client with circuit breaker and retries."""

    log = logging.getLogger(__name__)

    def __init__(
        self,
        base_url: str,
        *,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        check_interval: float = 30.0,
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
        self._session = aiohttp.ClientSession(timeout=self.timeout, ssl=self._ssl)
        self._check_interval = check_interval
        self._monitor_task = asyncio.create_task(
            monitor_dependency(
                base_url,
                self.circuit_breaker,
                self._health_check,
                self._reset_session,
                interval=check_interval,
                logger=self.log,
            )
        )

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
    async def _health_check(self) -> bool:
        try:
            async with aiohttp.ClientSession(
                timeout=self.timeout, ssl=self._ssl
            ) as sess:
                async with sess.head(self.base_url) as resp:
                    return resp.status < 500
        except Exception:
            return False

    async def _reset_session(self) -> None:
        await self._session.close()
        self._session = aiohttp.ClientSession(timeout=self.timeout, ssl=self._ssl)

    # ------------------------------------------------------------------
    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send an HTTP request with retries and tracing."""

        url = self.base_url + path
        headers: MutableMapping[str, str] = kwargs.pop("headers", {}) or {}
        propagate_context(headers)
        kwargs["headers"] = headers

        async def _do_request() -> Any:
            async with self.circuit_breaker:
                async with self._session.request(
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
            stop=stop_after_attempt(self.retries),
            wait=wait_exponential(),
            retry=retry_if_exception_type(aiohttp.ClientError),
        ):
            with attempt:
                return await _do_request()

    # ------------------------------------------------------------------
    async def close(self) -> None:
        if self._monitor_task:
            self._monitor_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._monitor_task
        await self._session.close()


__all__ = ["RestClient", "CircuitBreakerOpen"]
