"""Register fallback stubs for heavy optional dependencies.

Importing this module registers lightweight stubs for third-party libraries
that may not be installed in the runtime environment.  This helps keep the
project importable in minimal or testing setups where optional packages are
missing.
"""

from types import ModuleType
from unittest.mock import MagicMock

from optional_dependencies import register_stub


def _module(name: str, **attrs) -> ModuleType:
    """Return a simple module with ``attrs`` set as attributes."""

    mod = ModuleType(name)
    for key, value in attrs.items():
        setattr(mod, key, value)
    return mod


def setup_common_fallbacks() -> None:
    """Register fallback stubs for commonly optional dependencies."""

    # Explainability libraries -------------------------------------------------
    register_stub("shap", lambda: _module("shap", TreeExplainer=MagicMock()))

    register_stub("lime", lambda: _module("lime", lime_tabular=MagicMock()))
    register_stub(
        "lime.lime_tabular",
        lambda: _module("lime.lime_tabular", LimeTabularExplainer=MagicMock()),
    )

    # Machine learning frameworks ---------------------------------------------
    register_stub("torch", lambda: _module("torch"))
    register_stub("tensorflow", lambda: _module("tensorflow"))

    # Web / database libraries -------------------------------------------------
    _dash_stub = _module("dash")
    _dash_stub.html = _module("dash.html")
    _dash_stub.dcc = _module("dash.dcc")
    _dash_stub.dependencies = _module("dash.dependencies")
    _dash_stub._callback = _module("dash._callback")
    register_stub("dash", _dash_stub)
    register_stub("dash.html", lambda: _dash_stub.html)
    register_stub("dash.dcc", lambda: _dash_stub.dcc)
    register_stub("dash.dependencies", lambda: _dash_stub.dependencies)
    register_stub("dash._callback", lambda: _dash_stub._callback)

    register_stub(
        "asyncpg", lambda: _module("asyncpg", create_pool=MagicMock())
    )
    register_stub("psycopg2", lambda: _module("psycopg2", connect=MagicMock()))

    # Monitoring ---------------------------------------------------------------
    register_stub(
        "prometheus_client",
        lambda: _module(
            "prometheus_client",
            CollectorRegistry=MagicMock(),
            Counter=MagicMock(),
            Gauge=MagicMock(),
            Summary=MagicMock(),
            Histogram=MagicMock(),
        ),
    )


# Automatically set up fallbacks when this module is imported.
setup_common_fallbacks()

__all__ = ["setup_common_fallbacks"]
