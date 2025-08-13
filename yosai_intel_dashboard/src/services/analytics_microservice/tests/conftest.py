import pathlib
import sys
import types

SERVICES_PATH = pathlib.Path(__file__).resolve().parents[2]

# Provide a lightweight 'services' package to avoid heavy dependencies during test collection
services_stub = types.ModuleType("services")
services_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_stub)

# Stub hierarchical packages to prevent loading the full application
yosai_stub = types.ModuleType("yosai_intel_dashboard")
src_stub = types.ModuleType("yosai_intel_dashboard.src")
services_pkg_stub = types.ModuleType("yosai_intel_dashboard.src.services")
services_pkg_stub.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("yosai_intel_dashboard", yosai_stub)
sys.modules.setdefault("yosai_intel_dashboard.src", src_stub)
sys.modules.setdefault("yosai_intel_dashboard.src.services", services_pkg_stub)
