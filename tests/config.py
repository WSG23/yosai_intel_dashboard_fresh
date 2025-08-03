"""Central test configuration utilities.

Importing this module initialises the test environment by:
- setting required environment variables
- ensuring the project root is importable
- registering lightweight stubs for optional third‑party packages

It also exposes a couple of small fixtures used across the suite.
"""
from __future__ import annotations

import os
import sys
import types
from pathlib import Path

import pytest
from optional_dependencies import register_stub

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def set_test_environment() -> None:
    """Populate minimal environment variables for tests."""
    os.environ.setdefault("YOSAI_ENV", "testing")
    os.environ.setdefault("FLASK_ENV", "testing")
    os.environ.setdefault("SECRET_KEY", "testing")
    # enable lightweight implementations for optional services
    os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")


def add_project_root_to_sys_path() -> None:
    """Ensure the repository root is importable."""
    root_str = str(PROJECT_ROOT)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)


def register_dependency_stubs() -> None:
    """Register lightweight stubs for optional dependencies."""

    def _simple_module(name: str, **attrs: object) -> types.ModuleType:
        mod = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        return mod

    register_stub("hvac", _simple_module("hvac", Client=object))
    sys.modules.setdefault("hvac", _simple_module("hvac", Client=object))

    class _DummyFernet:
        def __init__(self, *a, **k):
            ...

        @staticmethod
        def generate_key() -> bytes:
            return b""

        def encrypt(self, data: bytes) -> bytes:
            return data

        def decrypt(self, data: bytes) -> bytes:
            return data

    register_stub(
        "cryptography.fernet",
        _simple_module("cryptography.fernet", Fernet=_DummyFernet),
    )
    sys.modules.setdefault(
        "cryptography.fernet", _simple_module("cryptography.fernet", Fernet=_DummyFernet)
    )

    register_stub("boto3", _simple_module("boto3", client=lambda *a, **k: object()))
    sys.modules.setdefault(
        "boto3", _simple_module("boto3", client=lambda *a, **k: object())
    )

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
    sys.modules.setdefault(
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
    sys.modules.setdefault(
        "asyncpg", _simple_module("asyncpg", create_pool=lambda *a, **k: None)
    )
    try:
        import httpx  # noqa: F401
    except Exception:  # pragma: no cover - fallback when httpx unavailable
        register_stub(
            "httpx",
            _simple_module(
                "httpx", ASGITransport=object, AsyncClient=object, Response=object
            ),
        )
        sys.modules.setdefault(
            "httpx",
            _simple_module(
                "httpx", ASGITransport=object, AsyncClient=object, Response=object
            ),
        )
    register_stub("structlog", _simple_module("structlog", BoundLogger=object))
    sys.modules.setdefault("structlog", _simple_module("structlog", BoundLogger=object))
    register_stub("confluent_kafka", _simple_module("confluent_kafka"))
    sys.modules.setdefault("confluent_kafka", _simple_module("confluent_kafka"))

    _dash = _simple_module("dash", Dash=object)
    _dash.html = _simple_module("dash.html")
    _dash.dcc = _simple_module("dash.dcc")
    _dash.dependencies = _simple_module(
        "dash.dependencies", Input=object, Output=object, State=object
    )
    _dash._callback = _simple_module("dash._callback")
    register_stub("dash", _dash)
    register_stub("dash.html", _dash.html)
    register_stub("dash.dcc", _dash.dcc)
    register_stub("dash.dependencies", _dash.dependencies)
    register_stub("dash._callback", _dash._callback)
    register_stub(
        "dash_bootstrap_components", _simple_module("dash_bootstrap_components")
    )
    sys.modules.setdefault("dash", _dash)
    sys.modules.setdefault("dash.html", _dash.html)
    sys.modules.setdefault("dash.dcc", _dash.dcc)
    sys.modules.setdefault("dash.dependencies", _dash.dependencies)
    sys.modules.setdefault("dash._callback", _dash._callback)
    sys.modules.setdefault(
        "dash_bootstrap_components", _simple_module("dash_bootstrap_components")
    )

    class _DummyRedis:
        @classmethod
        def from_url(cls, url):
            return cls()

        def pipeline(self):
            return self

        def incr(self, *a, **k):
            pass

        def expire(self, *a, **k):
            pass

        def execute(self):
            return (0, None)

        def ttl(self, key):
            return 0

    _redis = _simple_module("redis", Redis=_DummyRedis)
    _redis.asyncio = _simple_module("redis.asyncio")
    register_stub("redis", _redis)
    register_stub("redis.asyncio", _redis.asyncio)
    register_stub("requests", _simple_module("requests"))
    sys.modules.setdefault("redis", _redis)
    sys.modules.setdefault("redis.asyncio", _redis.asyncio)
    sys.modules.setdefault("requests", _simple_module("requests"))

    config_pkg = _simple_module("yosai_intel_dashboard.src.infrastructure.config")
    config_pkg.__path__ = [
        str(PROJECT_ROOT / "yosai_intel_dashboard" / "src" / "infrastructure" / "config")
    ]
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.infrastructure.config", config_pkg
    )

    services_db_pkg = _simple_module("yosai_intel_dashboard.src.services.database")
    services_db_pkg.__path__ = [
        str(PROJECT_ROOT / "yosai_intel_dashboard" / "src" / "database")
    ]
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.services.database", services_db_pkg
    )

    class _MockConnection:
        def __init__(self):
            self._connected = True

        def health_check(self):
            return self._connected

        def close(self):
            self._connected = False

    db_manager_stub = _simple_module(
        "yosai_intel_dashboard.src.infrastructure.config.database_manager",
        MockConnection=_MockConnection,
    )
    sys.modules.setdefault(
        "yosai_intel_dashboard.src.infrastructure.config.database_manager",
        db_manager_stub,
    )


# Run configuration steps on import
set_test_environment()
add_project_root_to_sys_path()
register_dependency_stubs()

from .fake_configuration import FakeConfiguration  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory path."""
    return tmp_path


@pytest.fixture
def fake_unicode_processor():
    """Return the reusable fake unicode processor."""
    from .fake_unicode_processor import FakeUnicodeProcessor

    return FakeUnicodeProcessor()

