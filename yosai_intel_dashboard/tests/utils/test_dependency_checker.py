from pathlib import Path
import sys
import types

# ensure repo root on path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

# stub heavy dependencies required by imported modules
sys.modules.setdefault("redis", types.ModuleType("redis"))
sys.modules.setdefault("redis.asyncio", types.ModuleType("redis.asyncio"))
sys.modules.setdefault("numpy", types.ModuleType("numpy"))
pandas_stub = types.ModuleType("pandas")


class DataFrame:  # pragma: no cover - lightweight stub
    pass


pandas_stub.DataFrame = DataFrame
sys.modules.setdefault("pandas", pandas_stub)
sys.modules.setdefault("psutil", types.ModuleType("psutil"))
sys.modules.setdefault("yaml", types.ModuleType("yaml"))
d_dash = types.ModuleType("dash")
d_dash.__path__ = []

class Dash:  # pragma: no cover - lightweight stub
    pass


deps_mod = types.ModuleType("dash.dependencies")


class _Dep:  # pragma: no cover - lightweight stub
    pass


deps_mod.Input = deps_mod.Output = deps_mod.State = _Dep
d_dash.Dash = Dash
d_dash.dependencies = deps_mod
sys.modules.setdefault("dash", d_dash)
sys.modules.setdefault("dash.dependencies", deps_mod)
prom_client = types.ModuleType("prometheus_client")
prom_client.__path__ = []  # mark as package
prom_client.REGISTRY = object()

class Counter:  # pragma: no cover - lightweight stub
    def __init__(self, *args, **kwargs):
        pass


class CollectorRegistry:  # pragma: no cover - lightweight stub
    pass


core_mod = types.ModuleType("prometheus_client.core")
core_mod.CollectorRegistry = CollectorRegistry
prom_client.Counter = Counter
prom_client.core = core_mod
sys.modules.setdefault("prometheus_client", prom_client)
sys.modules.setdefault("prometheus_client.core", core_mod)
pydantic_stub = types.ModuleType("pydantic")


class BaseModel:  # pragma: no cover - lightweight stub
    pass


def Field(*args, **kwargs):  # pragma: no cover - lightweight stub
    return None


pydantic_stub.BaseModel = BaseModel
pydantic_stub.Field = Field
pydantic_stub.ValidationError = Exception
sys.modules.setdefault("pydantic", pydantic_stub)
sys.modules.setdefault("jsonschema", types.ModuleType("jsonschema"))

# Create minimal package structure to load dependency_checker without heavy imports
yosai_pkg = types.ModuleType("yosai_intel_dashboard")
src_pkg = types.ModuleType("yosai_intel_dashboard.src")
utils_pkg = types.ModuleType("yosai_intel_dashboard.src.utils")
repo_pkg = types.ModuleType("yosai_intel_dashboard.src.repository")
yosai_pkg.__path__ = []
src_pkg.__path__ = []
utils_pkg.__path__ = []
repo_pkg.__path__ = []
sys.modules.setdefault("yosai_intel_dashboard", yosai_pkg)
sys.modules.setdefault("yosai_intel_dashboard.src", src_pkg)
sys.modules.setdefault("yosai_intel_dashboard.src.utils", utils_pkg)
sys.modules.setdefault("yosai_intel_dashboard.src.repository", repo_pkg)
sys.modules.setdefault("yosai_intel_dashboard.tests", types.ModuleType("yosai_intel_dashboard.tests"))
yosai_pkg.src = src_pkg
src_pkg.utils = utils_pkg
src_pkg.repository = repo_pkg

import importlib.util

req_module_path = Path(__file__).resolve().parents[2] / "src" / "repository" / "requirements.py"
spec_req = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.repository.requirements", req_module_path
)
requirements = importlib.util.module_from_spec(spec_req)
sys.modules[spec_req.name] = requirements
spec_req.loader.exec_module(requirements)  # type: ignore[union-attr]

module_path = Path(__file__).resolve().parents[2] / "src" / "utils" / "dependency_checker.py"
spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.utils.dependency_checker", module_path
)
dependency_checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dependency_checker
spec.loader.exec_module(dependency_checker)  # type: ignore[union-attr]
utils_pkg.dependency_checker = dependency_checker
DependencyChecker = dependency_checker.DependencyChecker


class StubRepo:
    def get_packages(self):
        return ["flask-babel"]


def test_dependency_checker_uses_repository(monkeypatch):
    captured = {}

    def fake_check(packages):
        captured["packages"] = packages
        return []

    checker = DependencyChecker(StubRepo())
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.utils.dependency_checker.check_dependencies",
        fake_check,
    )

    checker.verify_requirements()
    assert captured["packages"] == ["flask_babel"]

