from __future__ import annotations

import gc
import importlib
import importlib.machinery
import importlib.util
import logging
import os
import pathlib
import sys
import types

# Ensure repository root is on path
ROOT = pathlib.Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Tune garbage collection behaviour.  The higher thresholds reduce the
# frequency of collections for long-running services while keeping memory
# usage bounded.
gc.set_threshold(1000, 10, 10)

# Allow short-lived helper processes to skip the collector entirely once
# they have released resources.  Opt in via ``SHORT_LIVED_PROCESS=1``.
if os.getenv("SHORT_LIVED_PROCESS") == "1":
    gc.collect()
    gc.disable()

# Provide lightweight service stubs for environments without full dependencies
if "services" not in sys.modules:
    services_pkg = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("services", None)
    )
    services_pkg.__path__ = [str(ROOT / "services")]
    sys.modules["services"] = services_pkg

# Ensure package alias used by tests points to the lightweight stub
if "services" in sys.modules and "yosai_intel_dashboard.src.services" not in sys.modules:
    yf_services = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("yosai_intel_dashboard.src.services", None)
    )
    yf_services.__path__ = [str(ROOT / "yosai_intel_dashboard" / "src" / "services")]
    sys.modules["yosai_intel_dashboard.src.services"] = yf_services

if "services.resilience" not in sys.modules:
    resilience_pkg = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec("services.resilience", None)
    )
    resilience_pkg.__path__ = [str(ROOT / "services" / "resilience")]
    # Populate the package with our lightweight circuit breaker implementation
    # so that ``from yosai_intel_dashboard.src.services.resilience import CircuitBreaker`` works even in
    # environments where the full application dependencies are missing.
    cb_path = ROOT / "services" / "resilience" / "circuit_breaker.py"
    if cb_path.exists():
        try:
            module = importlib.import_module("services.resilience.circuit_breaker")
        except OSError as exc:
            logging.warning("Skipping services.resilience.circuit_breaker: %s", exc)
        else:
            sys.modules["services.resilience.circuit_breaker"] = module
            resilience_pkg.circuit_breaker = module
            resilience_pkg.CircuitBreaker = module.CircuitBreaker
            resilience_pkg.CircuitBreakerOpen = module.CircuitBreakerOpen

    sys.modules["services.resilience"] = resilience_pkg

if "services.resilience.metrics" not in sys.modules:
    metrics_path = ROOT / "services" / "resilience" / "metrics.py"
    if metrics_path.exists():
        try:
            metrics_mod = importlib.import_module("services.resilience.metrics")
        except OSError as exc:
            logging.warning("Skipping services.resilience.metrics: %s", exc)
            metrics_mod = importlib.util.module_from_spec(
                importlib.machinery.ModuleSpec("services.resilience.metrics", None)
            )
            metrics_mod.circuit_breaker_state = lambda *a, **k: None
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

if "core" not in sys.modules:
    core_pkg = types.ModuleType("core")
    core_pkg.__path__ = [str(ROOT / "yosai_intel_dashboard" / "src" / "core")]
    sys.modules["core"] = core_pkg
