"""Centralised optional dependency loader.

This module defines a small registry of optional dependencies used
throughout the project.  ``import_optional`` attempts to import a module
and falls back to a stub implementation when the dependency is not
installed.  The goal is to allow production code and tests to run even
when heavy optional packages are missing.

Example
-------
>>> from optional_dependencies import import_optional
>>> shap = import_optional('shap')
>>> if shap:
...     shap.TreeExplainer(...)
"""

from __future__ import annotations

import importlib
import logging
import types
from typing import Any, Callable, Dict

from yosai_intel_dashboard.src.infrastructure.monitoring.missing_dependencies import (
    missing_dependencies,
)

logger = logging.getLogger(__name__)

# Some optional packages are truly optional and should not produce
# noisy warnings when absent.
_NO_WARN_DEPS = {"cryptography", "cryptography.fernet"}


# ---------------------------------------------------------------------------
# Registry handling
_fallbacks: Dict[str, Callable[[], Any] | Any] = {}


def register_fallback(name: str, factory: Callable[[], Any] | Any) -> None:
    """Register a fallback factory for ``name``.

    ``factory`` may be a module instance or a callable returning one.
    The value is returned when :func:`import_optional` cannot import
    ``name``.
    """

    _fallbacks[name] = factory


# ``register_stub`` is kept for backwards compatibility with older tests
register_stub = register_fallback


# ---------------------------------------------------------------------------
# Optional import helper


def import_optional(name: str, fallback: Any | None = None) -> Any | None:
    """Attempt to import ``name`` returning a fallback on failure.

    Parameters
    ----------
    name:
        Dotted module path or ``pkg.mod.Class``.  If importing fails a
        registered stub or ``fallback`` is returned.  A warning is logged.
    fallback:
        Optional explicit fallback overriding any registered stub.
    """

    try:
        module = importlib.import_module(module_name)
        return getattr(module, attr) if attr else module
    except Exception as exc:  # pragma: no cover - defensive
        log = (
            logger.info
            if name in _NO_WARN_DEPS or module_name in _NO_WARN_DEPS
            else logger.warning
        )
        log("Optional dependency '%s' unavailable: %s", name, exc)

        missing_dependencies.labels(dependency=name).inc()
        value = _fallbacks.get(name) or _fallbacks.get(module_name) or fallback
        if callable(value):
            return value()
        return value



def is_available(name: str) -> bool:
    """Return ``True`` if ``name`` can be imported."""

    try:
        importlib.import_module(name)
        return True
    except Exception:  # pragma: no cover - defensive
        return False


__all__ = ["import_optional", "is_available", "register_fallback", "register_stub"]


# ---------------------------------------------------------------------------
# Default stubs for commonly optional packages


def _simple_module(name: str, **attrs: Any) -> types.ModuleType:
    mod = types.ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


# hvac ----------------------------------------------------------------------
register_fallback("hvac", lambda: _simple_module("hvac", Client=object))


# cryptography.fernet -------------------------------------------------------
class _DummyFernet:
    def __init__(self, *a: Any, **k: Any) -> None: ...

    @staticmethod
    def generate_key() -> bytes:  # pragma: no cover - simple stub
        return b""

    def encrypt(self, data: bytes) -> bytes:  # pragma: no cover - simple stub
        return data

    def decrypt(self, data: bytes) -> bytes:  # pragma: no cover - simple stub
        return data


register_fallback(
    "cryptography.fernet",
    lambda: _simple_module("cryptography.fernet", Fernet=_DummyFernet),
)


# boto3 ---------------------------------------------------------------------
register_fallback(
    "boto3", lambda: _simple_module("boto3", client=lambda *a, **k: object())
)


# mlflow --------------------------------------------------------------------
class _DummyRun:
    def __init__(self) -> None:
        self.info = types.SimpleNamespace(run_id="run")

    def __enter__(self) -> "_DummyRun":  # pragma: no cover - simple stub
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - simple stub
        pass


def _mlflow_stub() -> types.ModuleType:
    return _simple_module(
        "mlflow",
        start_run=lambda *a, **k: _DummyRun(),
        log_metric=lambda *a, **k: None,
        log_artifact=lambda *a, **k: None,
        log_text=lambda *a, **k: None,
        set_tracking_uri=lambda *a, **k: None,
    )


register_fallback("mlflow", _mlflow_stub)


# asyncpg -------------------------------------------------------------------
register_fallback(
    "asyncpg", lambda: _simple_module("asyncpg", create_pool=lambda *a, **k: None)
)


# httpx ---------------------------------------------------------------------
register_fallback(
    "httpx",
    lambda: _simple_module("httpx", ASGITransport=object, AsyncClient=object),
)


# structlog -----------------------------------------------------------------
register_fallback("structlog", lambda: _simple_module("structlog", BoundLogger=object))


# confluent_kafka -----------------------------------------------------------
register_fallback("confluent_kafka", lambda: _simple_module("confluent_kafka"))


# dash and friends ----------------------------------------------------------
_dash_stub = _simple_module("dash")
_dash_stub.html = _simple_module("dash.html")
_dash_stub.dcc = _simple_module("dash.dcc")
_dash_stub.dependencies = _simple_module("dash.dependencies")
_dash_stub._callback = _simple_module("dash._callback")
register_fallback("dash", _dash_stub)
register_fallback("dash.html", lambda: _dash_stub.html)
register_fallback("dash.dcc", lambda: _dash_stub.dcc)
register_fallback("dash.dependencies", lambda: _dash_stub.dependencies)
register_fallback("dash._callback", lambda: _dash_stub._callback)
register_fallback("dash_bootstrap_components", lambda: _simple_module("dbc"))


# redis ---------------------------------------------------------------------
_redis_stub = _simple_module("redis")
_redis_stub.asyncio = _simple_module("redis.asyncio")
register_fallback("redis", _redis_stub)
register_fallback("redis.asyncio", lambda: _redis_stub.asyncio)


# requests ------------------------------------------------------------------
register_fallback("requests", lambda: _simple_module("requests"))
