from __future__ import annotations

import sys
import types
from pathlib import Path


def setup_common_fallbacks() -> None:
    """Install lightweight stubs for optional packages used in tests."""
    try:  # ensure default optional dependency stubs are registered
        import optional_dependencies  # noqa: F401
    except Exception:  # pragma: no cover - best effort
        pass

    services_path = Path(__file__).resolve().parents[3] / "services"
    services_stub = types.ModuleType("services")
    services_stub.__path__ = [str(services_path)]
    sys.modules.setdefault("services", services_stub)

    # Basic prometheus_client stub used by metrics modules
    prom_stub = types.ModuleType("prometheus_client")
    prom_stub.Gauge = object  # type: ignore[attr-defined]
    prom_stub.Counter = object  # type: ignore[attr-defined]
    prom_stub.Histogram = object  # type: ignore[attr-defined]
    sys.modules.setdefault("prometheus_client", prom_stub)

    # Additional common third-party dependencies used across the
    # codebase.  During tests these heavy packages may not be
    # installed so we provide very small stand‑ins that satisfy
    # import statements.  Only attributes that are referenced in the
    # tests are provided.
    def _register(name: str, **attrs: object) -> None:
        """Ensure ``name`` can be imported by providing a minimal stub.

        If the real package is available it is left untouched.  Otherwise a
        new lightweight module is inserted into ``sys.modules`` and populated
        with the supplied ``attrs``.
        """

        try:  # prefer real package if available
            __import__(name)
            return
        except Exception:
            pass

        parts = name.split(".")
        module = None
        for i in range(1, len(parts) + 1):
            pkg_name = ".".join(parts[:i])
            mod = sys.modules.get(pkg_name)
            if mod is None:
                mod = types.ModuleType(parts[i - 1])
                mod.__path__ = []  # type: ignore[attr-defined]
                sys.modules[pkg_name] = mod
            module = mod
        for key, value in attrs.items():
            setattr(module, key, value)

    _register("pydantic", BaseModel=type("BaseModel", (), {}))
    _register("numpy")
    _register("pandas", DataFrame=type("DataFrame", (), {}))
    _register("requests")
    _register("aiohttp")
    _register("aiofiles")
    _register("sqlalchemy")
    _register("psycopg2")
    _register("starlette")
    _register("fastapi.responses")
    _register("flask.json")
    _register("flask_caching")
    _register("httpx")
    _register("joblib")
    _register("jose")
    _register("matplotlib")
    _register("pyotp")
    _register("websockets")
    _register("alembic")
    _register("cachetools")
    _register("bleach")
    _register("werkzeug")
    _register("dash")
    _register("testcontainers")

