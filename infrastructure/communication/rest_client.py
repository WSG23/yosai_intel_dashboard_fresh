from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any, MutableMapping
from uuid import uuid4

import aiohttp
import structlog

from .circuit_breaker import CircuitBreaker, CircuitBreakerOpen
from .protocols import ServiceClient


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0


class AsyncRestClient(ServiceClient):
    """Asynchronous HTTP client with retries and circuit breaker."""

    def __init__(
        self,
        base_url: str,
        *,
        timeout: float = 5.0,
        retry_policy: RetryPolicy | None = None,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retry_policy = retry_policy or RetryPolicy()
        self.circuit_breaker = CircuitBreaker(
            failure_threshold, recovery_timeout, name=base_url
        )
        self.log: structlog.BoundLogger = structlog.get_logger(__name__)

    # ------------------------------------------------------------------
    async def request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = self.base_url + path
        headers: MutableMapping[str, str] = kwargs.pop("headers", {}) or {}
        request_id = headers.get("X-Request-ID", uuid4().hex)
        headers["X-Request-ID"] = request_id
        kwargs["headers"] = headers
        attempt = 0
        delay = self.retry_policy.base_delay
        log = self.log.bind(request_id=request_id, url=url, method=method)

        while True:
            try:
                async with self.circuit_breaker:
                    async with aiohttp.ClientSession() as session:
                        async with session.request(
                            method,
                            url,
                            timeout=self.timeout,
                            **kwargs,
                        ) as resp:
                            log.info("request", status=resp.status)
                            resp.raise_for_status()
                            ctype = resp.headers.get("Content-Type", "")
                            if "application/json" in ctype:
                                return await resp.json()
                            return await resp.text()
            except CircuitBreakerOpen:
                log.warning("circuit_open")
                raise
            except Exception as exc:
                attempt += 1
                log.warning("request_failed", attempt=attempt, error=str(exc))
                if attempt >= self.retry_policy.max_attempts:
                    raise
                await asyncio.sleep(delay)
                delay = min(
                    delay * self.retry_policy.exponential_base,
                    self.retry_policy.max_delay,
                )


# ----------------------------------------------------------------------

def create_service_client(service_name: str) -> ServiceClient:
    """Create a service client resolving *service_name* URL from env vars."""
    env = f"{service_name.upper()}_SERVICE_URL"
    base_url = os.getenv(env, f"http://{service_name}")
    return AsyncRestClient(base_url)


__all__ = ["AsyncRestClient", "RetryPolicy", "create_service_client", "CircuitBreakerOpen"]
