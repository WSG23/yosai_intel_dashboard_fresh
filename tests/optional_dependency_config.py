"""Register test-time optional dependency stubs.

This module centralises all stub registrations used by the test-suite.
Importing it has the side effect of registering fallbacks with the
:mod:`optional_dependencies` registry so tests can run without optional
third-party packages.
"""
from __future__ import annotations

import types
from pathlib import Path

from optional_dependencies import register_stub


def _simple_module(name: str, **attrs: object) -> types.ModuleType:
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


# ---------------------------------------------------------------------------
# Lightweight services package used by tests
services_stub = _simple_module("services")
services_path = Path(__file__).resolve().parents[1] / "services"
services_stub.__path__ = [str(services_path)]
register_stub("services", services_stub)
register_stub("services.resilience", _simple_module("services.resilience"))
metrics_mod = _simple_module(
    "services.resilience.metrics",
    circuit_breaker_state=types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    ),
)
register_stub("services.resilience.metrics", metrics_mod)


# Core optional third-party libraries ---------------------------------------
register_stub("hvac", _simple_module("hvac", Client=object))

class _DummyFernet:
    def __init__(self, *a, **k): ...

    @staticmethod
    def generate_key() -> bytes:
        return b""

    def encrypt(self, data: bytes) -> bytes:
        return data

    def decrypt(self, data: bytes) -> bytes:
        return data

register_stub(
    "cryptography.fernet", _simple_module("cryptography.fernet", Fernet=_DummyFernet)
)

register_stub("boto3", _simple_module("boto3", client=lambda *a, **k: object()))

class _DummyRun:
    def __init__(self) -> None:
        self.info = types.SimpleNamespace(run_id="run")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

register_stub(
    "mlflow",
    _simple_module(
        "mlflow",
        start_run=lambda *a, **k: _DummyRun(),
        log_metric=lambda *a, **k: None,
        log_artifact=lambda *a, **k: None,
        log_text=lambda *a, **k: None,
        set_tracking_uri=lambda *a, **k: None,
    ),
)

register_stub("asyncpg", _simple_module("asyncpg", create_pool=lambda *a, **k: None))
register_stub(
    "httpx", _simple_module("httpx", ASGITransport=object, AsyncClient=object)
)
register_stub("structlog", _simple_module("structlog", BoundLogger=object))
register_stub("confluent_kafka", _simple_module("confluent_kafka"))

# Dash and related packages used by UI tests
_dash = _simple_module("dash")
_dash.html = _simple_module("dash.html")
_dash.dcc = _simple_module("dash.dcc")
_dash.dependencies = _simple_module("dash.dependencies")
_dash._callback = _simple_module("dash._callback")
register_stub("dash", _dash)
register_stub("dash.html", _dash.html)
register_stub("dash.dcc", _dash.dcc)
register_stub("dash.dependencies", _dash.dependencies)
register_stub("dash._callback", _dash._callback)
register_stub("dash_bootstrap_components", _simple_module("dash_bootstrap_components"))

# Redis and requests
_redis = _simple_module("redis")
_redis.asyncio = _simple_module("redis.asyncio")
register_stub("redis", _redis)
register_stub("redis.asyncio", _redis.asyncio)
register_stub("requests", _simple_module("requests"))

# No shap/lime stubs; tests will skip explainability features if missing
