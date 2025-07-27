import importlib
import pathlib
import sys

# Ensure repository root is on path and pre-import services package
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
try:
    services_pkg = importlib.import_module("services")
except Exception:
    services_pkg = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("services", None)
    )
    services_pkg.__path__ = [str(ROOT / "services")]
    sys.modules["services"] = services_pkg

if "services.resilience" not in sys.modules:
    resilience_pkg = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("services.resilience", None)
    )
    resilience_pkg.__path__ = [str(ROOT / "services" / "resilience")]
    sys.modules["services.resilience"] = resilience_pkg

if "services.resilience.metrics" not in sys.modules:
    try:
        importlib.import_module("services.resilience.metrics")
    except Exception:
        metrics_mod = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec("services.resilience.metrics", None)
        )
        metrics_mod.circuit_breaker_state = lambda *a, **k: None
        sys.modules["services.resilience.metrics"] = metrics_mod
