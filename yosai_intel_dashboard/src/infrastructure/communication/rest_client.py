from __future__ import annotations

import logging
import os
import ssl
import warnings
from dataclasses import dataclass
from typing import Any, MutableMapping

import aiohttp
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
    wait_random,
)

try:  # pragma: no cover - tracing is optional in tests
    from tracing import propagate_context
except Exception:  # pragma: no cover - graceful fallback when tracing deps missing

    def propagate_context(headers: MutableMapping[str, str]) -> None:  # type: ignore
        return None


from yosai_intel_dashboard.src.core.async_utils.async_circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpen,
)
from yosai_intel_dashboard.src.error_handling import ErrorHandler

from ..monitoring.request_metrics import request_retry_count, request_retry_delay


@dataclass
class RetryPolicy:
    """Configuration for async retry behaviour."""

    max_attempts: int = 3
    initial_delay: float = 0.1
    max_delay: float = 60.0
    exp_base: float = 2.0
    jitter: float = 0.1

    def build_wait(self):
        wait = wait_exponential(
            multiplier=self.initial_delay,
            max=self.max_delay,
            exp_base=self.exp_base,
        )
        if self.jitter:
            wait = wait + wait_random(0, self.jitter)
        return wait


class AsyncRestClient:
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
        retry_policy: RetryPolicy | None = None,
        mtls_cert: str | None = None,
        mtls_key: str | None = None,
        verify_ssl: bool = True,
        pool_size: int = 100,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.circuit_breaker = CircuitBreaker(
            failure_threshold, recovery_timeout, name=base_url
        )
        self.retry_policy = retry_policy or RetryPolicy(max_attempts=retries)
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._ssl = self._create_ssl_context(mtls_cert, mtls_key, verify_ssl)
        self._error_handler = ErrorHandler()
        self._pool_size = pool_size
        self._connector: aiohttp.TCPConnector | None = None
        self._session: aiohttp.ClientSession | None = None

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
    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            await self._reset_session()
        return self._session

    async def _health_check(self) -> bool:
        try:
            session = await self._get_session()
            async with session.head(self.base_url) as resp:
                return resp.status < 500
        except Exception:
            return False

    async def _reset_session(self) -> None:
        if self._session is not None:
            await self._session.close()
        self._connector = aiohttp.TCPConnector(limit=self._pool_size, ssl=self._ssl)
        self._session = aiohttp.ClientSession(
            timeout=self.timeout, connector=self._connector
        )

    # ------------------------------------------------------------------
    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        """Send an HTTP request with retries and tracing."""

        url = self.base_url + path
        headers: MutableMapping[str, str] = kwargs.pop("headers", {}) or {}
        propagate_context(headers)
        kwargs["headers"] = headers

        async def _do_request() -> Any:
            async with self.circuit_breaker:
                session = await self._get_session()
                async with session.request(method, url, **kwargs) as resp:
                    self.log.info("%s %s -> %s", method, url, resp.status)
                    resp.raise_for_status()
                    ctype = resp.headers.get("Content-Type", "")
                    if "application/json" in ctype:
                        return await resp.json()
                    return await resp.text()

        wait = self.retry_policy.build_wait()

        async for attempt in AsyncRetrying(
            retry=retry_if_exception_type(aiohttp.ClientError),
            stop=stop_after_attempt(self.retry_policy.max_attempts),
            wait=wait,
            reraise=True,
            before_sleep=self._record_retry,
        ):
            with attempt:
                return await _do_request()

    # ------------------------------------------------------------------
    @staticmethod
    def _record_retry(retry_state) -> None:
        request_retry_count.inc()
        if retry_state.next_action:
            request_retry_delay.observe(retry_state.next_action.sleep)

    async def close(self) -> None:
        if self._session is not None:
            await self._session.close()


def create_service_client(service_name: str) -> "AsyncRestClient":
    """Create a service client resolving *service_name* URL from env vars."""
    env = f"{service_name.upper()}_SERVICE_URL"
    base_url = os.getenv(env, f"http://{service_name}")
    return AsyncRestClient(base_url)


__all__ = [
    "AsyncRestClient",
    "RetryPolicy",
    "create_service_client",
    "CircuitBreakerOpen",
    "RestClient",
]


class RestClient(AsyncRestClient):
    """Deprecated synchronous-style client alias for :class:`AsyncRestClient`."""

    def __init__(self, *args, **kwargs) -> None:  # type: ignore[override]
        warnings.warn(
            "RestClient is deprecated; use AsyncRestClient",
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(*args, **kwargs)
