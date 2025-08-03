import importlib
import importlib.machinery
import importlib.util
import pathlib
import sys

# Ensure repository root is on path
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Provide lightweight service stubs for environments without full dependencies
if "services" not in sys.modules:
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
    # Populate the package with our lightweight circuit breaker implementation
    # so that ``from services.resilience import CircuitBreaker`` works even in
    # environments where the full application dependencies are missing.
    cb_path = ROOT / "services" / "resilience" / "circuit_breaker.py"
    if cb_path.exists():
        spec = importlib.util.spec_from_file_location(
            "services.resilience.circuit_breaker", cb_path
        )
        module = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(module)  # type: ignore[arg-type]
        sys.modules["services.resilience.circuit_breaker"] = module
        resilience_pkg.circuit_breaker = module
        resilience_pkg.CircuitBreaker = module.CircuitBreaker
        resilience_pkg.CircuitBreakerOpen = module.CircuitBreakerOpen

    sys.modules["services.resilience"] = resilience_pkg

if "services.resilience.metrics" not in sys.modules:
    metrics_path = ROOT / "services" / "resilience" / "metrics.py"
    if metrics_path.exists():
        spec = importlib.util.spec_from_file_location(
            "services.resilience.metrics", metrics_path
        )
        metrics_mod = importlib.util.module_from_spec(spec)
        assert spec.loader is not None
        spec.loader.exec_module(metrics_mod)  # type: ignore[arg-type]
    else:  # pragma: no cover - fallback when metrics not provided
        metrics_mod = importlib.util.module_from_spec(
            importlib.machinery.ModuleSpec("services.resilience.metrics", None)
        )
        metrics_mod.circuit_breaker_state = lambda *a, **k: None
    sys.modules["services.resilience.metrics"] = metrics_mod

if "hvac" not in sys.modules:
    hvac_mod = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("hvac", None)
    )
    hvac_mod.Client = object  # minimal stub for tests
    sys.modules["hvac"] = hvac_mod
