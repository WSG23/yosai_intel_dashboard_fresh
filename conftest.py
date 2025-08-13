import importlib.machinery
import importlib.util
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent

# Provide a lightweight stub for yosai_intel_dashboard.src.services
if "yosai_intel_dashboard.src.services" not in sys.modules:
    spec = importlib.machinery.ModuleSpec("yosai_intel_dashboard.src.services", None)
    pkg = importlib.util.module_from_spec(spec)
    pkg.__path__ = [str(ROOT / "yosai_intel_dashboard" / "src" / "services")]
    sys.modules["yosai_intel_dashboard.src.services"] = pkg
