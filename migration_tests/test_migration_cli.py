import importlib.util
import pathlib
import sys
import types

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
SERVICES_PATH = ROOT / "yosai_intel_dashboard" / "src" / "services"

# Stub out heavy optional dependencies
dash_stub = types.ModuleType("dash")
dash_stub.Dash = object
sys.modules.setdefault("dash", dash_stub)
deps_stub = types.ModuleType("dash.dependencies")
deps_stub.Input = deps_stub.Output = deps_stub.State = object
sys.modules.setdefault("dash.dependencies", deps_stub)
services_pkg = types.ModuleType("services")
services_pkg.__path__ = [str(SERVICES_PATH)]
sys.modules.setdefault("services", services_pkg)
cli_spec = importlib.util.spec_from_file_location(
    "services.migration.cli",
    SERVICES_PATH / "migration" / "cli.py",
)
migration_cli = importlib.util.module_from_spec(cli_spec)
cli_spec.loader.exec_module(migration_cli)


class DummyManager:
    def __init__(self) -> None:
        self.called = []

    async def migrate(self) -> None:
        self.called.append("run")

    async def rollback(self) -> None:
        self.called.append("rollback")

    async def status(self):
        self.called.append("status")
        return {"progress": {}, "failures": []}


def test_cli_status(monkeypatch):
    monkeypatch.setattr(migration_cli, "_build_manager", lambda args: DummyManager())
    rc = migration_cli.main(["status"])
    assert rc == 0
