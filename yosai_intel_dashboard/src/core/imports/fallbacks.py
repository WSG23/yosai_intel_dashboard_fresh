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

