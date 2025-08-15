import importlib.util
import sys
import types
from pathlib import Path

from flask import Flask

# Stub out heavy secret manager dependency during import
secret_stub = types.SimpleNamespace(validate_secrets=lambda: {})
sys.modules["yosai_intel_dashboard.src.core.secret_manager"] = secret_stub

# Build minimal package structure for dependency_checker
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
yosai_pkg.src = src_pkg
src_pkg.utils = utils_pkg
src_pkg.repository = repo_pkg

req_module_path = (
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "repository"
    / "requirements.py"
)
spec_req = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.repository.requirements", req_module_path
)
requirements = importlib.util.module_from_spec(spec_req)
sys.modules[spec_req.name] = requirements
spec_req.loader.exec_module(requirements)  # type: ignore[attr-defined]

# Load dependency_checker in isolation
module_path = (
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "utils"
    / "dependency_checker.py"
)
spec = importlib.util.spec_from_file_location(
    "yosai_intel_dashboard.src.utils.dependency_checker", module_path
)
dependency_checker = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = dependency_checker
spec.loader.exec_module(dependency_checker)  # type: ignore[attr-defined]
utils_pkg.dependency_checker = dependency_checker

# Load the health module
spec_health = importlib.util.spec_from_file_location(
    "health_module",
    Path(__file__).resolve().parents[1]
    / "yosai_intel_dashboard"
    / "src"
    / "core"
    / "app_factory"
    / "health.py",
)
health_module = importlib.util.module_from_spec(spec_health)
spec_health.loader.exec_module(health_module)  # type: ignore[attr-defined]
register_health_endpoints = health_module.register_health_endpoints


def test_health_endpoint_healthy(monkeypatch):
    """Health endpoint returns healthy when dependencies are satisfied."""
    monkeypatch.setattr(
        dependency_checker,
        "check_dependencies",
        lambda packages=None: [],
    )

    app = Flask(__name__)
    register_health_endpoints(app)
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json() == {"status": "healthy"}


def test_health_endpoint_dependency_failure(monkeypatch):
    """Health endpoint reports missing dependencies with 503."""
    monkeypatch.setattr(
        dependency_checker,
        "check_dependencies",
        lambda packages=None: ["database"],
    )

    app = Flask(__name__)
    register_health_endpoints(app)
    client = app.test_client()

    resp = client.get("/health")
    assert resp.status_code == 503
    assert resp.get_json() == {
        "status": "unhealthy",
        "missing": ["database"],
    }
