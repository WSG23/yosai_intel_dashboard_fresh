"""Register test-time optional dependency stubs.

This module centralises all stub registrations used by the test-suite.
Importing it has the side effect of registering fallbacks with the
:mod:`optional_dependencies` registry so tests can run without optional
third-party packages.
"""
from __future__ import annotations

import types
from pathlib import Path

from .import_helpers import install_stub, simple_module, simple_stub


# ---------------------------------------------------------------------------
# Lightweight services package used by tests
services_stub = simple_module("services")
services_path = Path(__file__).resolve().parents[1] / "services"
services_stub.__path__ = [str(services_path)]
install_stub("services", services_stub)
simple_stub("services.resilience")
metrics_mod = simple_stub(
    "services.resilience.metrics",
    circuit_breaker_state=types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    ),
)


# Core optional third-party libraries ---------------------------------------
simple_stub("hvac", Client=object)

class _DummyFernet:
    def __init__(self, *a, **k): ...

    @staticmethod
    def generate_key() -> bytes:
        return b""

    def encrypt(self, data: bytes) -> bytes:
        return data

    def decrypt(self, data: bytes) -> bytes:
        return data

simple_stub("cryptography.fernet", Fernet=_DummyFernet)

simple_stub("boto3", client=lambda *a, **k: object())

class _DummyRun:
    def __init__(self) -> None:
        self.info = types.SimpleNamespace(run_id="run")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass

simple_stub(
    "mlflow",
    start_run=lambda *a, **k: _DummyRun(),
    log_metric=lambda *a, **k: None,
    log_artifact=lambda *a, **k: None,
    log_text=lambda *a, **k: None,
    set_tracking_uri=lambda *a, **k: None,
)

simple_stub("asyncpg", create_pool=lambda *a, **k: None)
simple_stub("httpx", ASGITransport=object, AsyncClient=object)
simple_stub("structlog", BoundLogger=object)
simple_stub("confluent_kafka")

# Dash and related packages used by UI tests
_dash = simple_stub("dash", Dash=object)
_dash.html = simple_stub("dash.html")
_dash.dcc = simple_stub("dash.dcc")
_dash.dependencies = simple_stub(
    "dash.dependencies", Input=object, Output=object, State=object
)
_dash._callback = simple_stub("dash._callback")
install_stub("dash", _dash)
install_stub("dash.html", _dash.html)
install_stub("dash.dcc", _dash.dcc)
install_stub("dash.dependencies", _dash.dependencies)
install_stub("dash._callback", _dash._callback)
simple_stub("dash_bootstrap_components")

# Redis and requests
_redis = simple_stub("redis")
_redis.asyncio = simple_stub("redis.asyncio")
install_stub("redis", _redis)
install_stub("redis.asyncio", _redis.asyncio)
simple_stub("requests")

# No shap/lime stubs; tests will skip explainability features if missing
