"""Simple Consul-based service discovery helper."""

from __future__ import annotations

import os
from typing import Optional

import requests


class ConsulServiceDiscovery:
    """Query Consul's HTTP API for service locations.

    Only a very small subset of Consul's functionality is implemented.  The
    helper returns the first registered address for a given service name or
    ``None`` if no service is known.  Failures are swallowed to keep callers
    resilient when Consul is unavailable.
    """

    def __init__(self, *, host: str | None = None, port: int | None = None) -> None:
        self.host = host or os.getenv("CONSUL_HOST", "localhost")
        self.port = port or int(os.getenv("CONSUL_PORT", "8500"))

    # ------------------------------------------------------------------
    def get_service(self, name: str) -> Optional[str]:
        """Return ``host:port`` for *name* if available."""

        url = f"http://{self.host}:{self.port}/v1/catalog/service/{name}"
        try:
            resp = requests.get(url, timeout=2)
            resp.raise_for_status()
            data = resp.json()
            if not data:
                return None
            entry = data[0]
            address = entry.get("ServiceAddress") or entry.get("Address")
            port = entry.get("ServicePort")
            if address and port:
                return f"{address}:{port}"
        except Exception:
            pass
        return None


__all__ = ["ConsulServiceDiscovery"]
