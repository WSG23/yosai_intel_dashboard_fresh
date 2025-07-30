from __future__ import annotations

import asyncio
import os
import socket
from typing import List

import aiohttp
from cachetools import TTLCache


class K8sResolver:
    """Resolve Kubernetes service DNS entries with health checks and caching."""

    def __init__(self, namespace: str | None = None, *, cache_ttl: int = 30) -> None:
        self.namespace = namespace or os.getenv("K8S_NAMESPACE", "default")
        # Map "service:port" -> List[str]
        self._cache: TTLCache[str, List[str]] = TTLCache(maxsize=128, ttl=cache_ttl)

    # ------------------------------------------------------------------
    async def _resolve_dns(self, service: str, port: int) -> List[str]:
        host = f"{service}.{self.namespace}.svc.cluster.local"
        loop = asyncio.get_running_loop()
        infos = await loop.getaddrinfo(host, port, type=socket.SOCK_STREAM)
        return sorted({info[4][0] for info in infos})

    # ------------------------------------------------------------------
    async def _check_health(self, address: str, port: int) -> bool:
        url = f"http://{address}:{port}/health/ready"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url, timeout=aiohttp.ClientTimeout(total=1.0)
                ) as resp:
                    return resp.status < 400
        except Exception:
            return False

    # ------------------------------------------------------------------
    async def resolve(self, service: str, port: int = 80) -> List[str]:
        """Return healthy base URLs for *service* using Kubernetes DNS."""
        key = f"{service}:{port}"
        cached = self._cache.get(key)
        if cached is not None:
            return cached

        try:
            addresses = await self._resolve_dns(service, port)
        except socket.gaierror:
            env_var = f"{service.upper().replace('-', '_')}_SERVICE_URL"
            env_url = os.getenv(env_var)
            if env_url:
                self._cache[key] = [env_url]
                return [env_url]
            return []

        healthy: List[str] = []
        for addr in addresses:
            if await self._check_health(addr, port):
                healthy.append(f"http://{addr}:{port}")
        self._cache[key] = healthy
        return healthy
