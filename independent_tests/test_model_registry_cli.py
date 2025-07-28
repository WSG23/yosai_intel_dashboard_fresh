import importlib.util
from pathlib import Path
import types
import sys

if "boto3" not in sys.modules:
    sys.modules["boto3"] = types.ModuleType("boto3")
if "mlflow" not in sys.modules:
    mlflow_stub = types.ModuleType("mlflow")

    class DummyRun:
        def __init__(self):
            self.info = types.SimpleNamespace(run_id="run")

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            pass

    mlflow_stub.start_run = lambda *a, **k: DummyRun()
    mlflow_stub.log_metric = lambda *a, **k: None
    mlflow_stub.log_artifact = lambda *a, **k: None
    mlflow_stub.log_text = lambda *a, **k: None
    mlflow_stub.set_tracking_uri = lambda *a, **k: None
    sys.modules["mlflow"] = mlflow_stub
if "requests" not in sys.modules:
    sys.modules["requests"] = types.ModuleType("requests")

import pytest

path = Path(__file__).resolve().parents[1] / "models" / "ml" / "model_registry.py"
spec = importlib.util.spec_from_file_location("model_registry", path)
mr = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(mr)
ModelRegistry = mr.ModelRegistry

if "services.resilience" not in sys.modules:
    sys.modules["services.resilience"] = types.ModuleType("services.resilience")
if "services.resilience.metrics" not in sys.modules:
    metrics_stub = types.ModuleType("services.resilience.metrics")
    metrics_stub.circuit_breaker_state = types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    )
    sys.modules["services.resilience.metrics"] = metrics_stub


class DummyS3:
    def upload_file(self, *a, **k):
        pass

    def download_file(self, *a, **k):
        pass


@pytest.fixture
def cli_module():
    path = Path(__file__).resolve().parents[1] / "scripts" / "model_registry_cli.py"
    sys.modules.setdefault("models", types.ModuleType("models"))
    sys.modules.setdefault("models.ml", types.ModuleType("models.ml"))
    sys.modules["models.ml.model_registry"] = mr
    spec = importlib.util.spec_from_file_location("model_registry_cli", path)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_cli_list_and_activate(tmp_path, cli_module, capsys):
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
        ["--db-url", db_url, "--bucket", "bucket", "activate", "demo", rec2.version]
    )
    active = registry.get_model("demo", active_only=True)
    assert active.version == rec2.version
