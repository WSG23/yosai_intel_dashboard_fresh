"""Simple Consul-based service discovery helper."""

from __future__ import annotations

import os
from typing import Any

import requests


def _consul_addr() -> str:
    """Return host:port for the Consul agent from env vars."""
    host = os.getenv("CONSUL_HOST", "localhost")
    port = os.getenv("CONSUL_PORT", "8500")
    return f"{host}:{port}"


def resolve_service(name: str) -> str:
    """
    Resolve ``name`` to ``host:port`` using the Consul catalog API.

    Raises ``RuntimeError`` when the service cannot be found.
    """
    url = f"http://{_consul_addr()}/v1/catalog/service/{name}"
    resp = requests.get(url, timeout=2)
    resp.raise_for_status()
    data: list[dict[str, Any]] = resp.json()
    if not data:
        raise RuntimeError(f"service {name} not found")
    svc = data[0]
    return f"{svc['ServiceAddress']}:{svc['ServicePort']}"


__all__ = ["resolve_service"]

