import importlib.util
import sys
import types
from pathlib import Path

import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Dynamically load the ModelRegistry implementation while providing lightweight
# stubs for heavy optional dependencies. ``tests.conftest`` already injects
# dummy ``boto3`` and ``mlflow`` modules when they are not available.
path = (
    Path(__file__).resolve().parents[2]
    / "src"
    / "intel_analysis_service"
    / "ml"
    / "model_registry.py"
)
spec = importlib.util.spec_from_file_location("model_registry", path)
mr = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mr
assert spec.loader
spec.loader.exec_module(mr)
ModelRegistry = mr.ModelRegistry


class DummyS3:
    def upload_file(self, *a, **k):
        pass

    def download_file(self, *a, **k):
        pass


@pytest.fixture
def cli_module(monkeypatch: pytest.MonkeyPatch):
    path = Path(__file__).resolve().parents[2] / "scripts" / "model_registry_cli.py"
    safe_import(
        "yosai_intel_dashboard.models",
        types.ModuleType("yosai_intel_dashboard.models"),
    )
    safe_import(
        "yosai_intel_dashboard.models.ml",
        types.ModuleType("yosai_intel_dashboard.models.ml"),
    )
    safe_import("yosai_intel_dashboard.models.ml.model_registry", mr)
    spec = importlib.util.spec_from_file_location("model_registry_cli", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_cli_list_and_activate(tmp_path: Path, cli_module, capsys):
    db_path = tmp_path / "reg.db"
    db_url = f"sqlite:///{db_path}"
    registry = ModelRegistry(db_url, "bucket", s3_client=DummyS3())

    m1 = tmp_path / "m1.bin"
    m1.write_text("x")
    rec1 = registry.register_model("demo", str(m1), {"accuracy": 0.8}, "h1")
    registry.set_active_version("demo", rec1.version)

    m2 = tmp_path / "m2.bin"
    m2.write_text("y")
    rec2 = registry.register_model("demo", str(m2), {"accuracy": 0.9}, "h2")

    # patch ModelRegistry to avoid real S3 usage
    cli_module.ModelRegistry = lambda db_url, bucket: ModelRegistry(
        db_url, bucket, s3_client=DummyS3()
    )

    cli_module.main(["--db-url", db_url, "--bucket", "bucket", "list", "demo"])
    out = capsys.readouterr().out
    assert rec1.version in out and rec2.version in out

    cli_module.main(
        [
            "--db-url",
            db_url,
            "--bucket",
            "bucket",
            "activate",
            "demo",
            rec2.version,
        ]
    )
    active = registry.get_model("demo", active_only=True)
    assert active.version == rec2.version
