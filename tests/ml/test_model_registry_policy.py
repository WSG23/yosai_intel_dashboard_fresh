import importlib.util
from pathlib import Path
import types

import pytest


class DummyS3:
    def upload_file(self, *a, **k):
        pass

    def download_file(self, *a, **k):
        pass


class DummyRun:
    def __init__(self):
        self.info = types.SimpleNamespace(run_id="run")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        pass


class DummyMlflow:
    def start_run(self):
        return DummyRun()

    def log_metric(self, *a, **k):
        pass

    def log_artifact(self, *a, **k):
        pass

    def set_tracking_uri(self, *a, **k):
        pass


@pytest.fixture
def registry(monkeypatch, tmp_path):
    path = (
        Path(__file__).resolve().parents[2]
        / "yosai_intel_dashboard"
        / "src"
        / "models"
        / "ml"
        / "model_registry.py"
    )
    spec = importlib.util.spec_from_file_location("model_registry", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "mlflow", DummyMlflow())
    return module.ModelRegistry(
        "sqlite:///:memory:",
        bucket="bucket",
        s3_client=DummyS3(),
        drift_thresholds={"accuracy": 0.05},
    )


def test_activation_respects_drift_threshold(tmp_path, registry):
    p1 = tmp_path / "m1.bin"
    p1.write_text("a")
    registry.register_model("m", str(p1), {"accuracy": 0.9}, "h1", version="0.1.0")
    registry.set_active_version("m", "0.1.0")
    p2 = tmp_path / "m2.bin"
    p2.write_text("b")
    registry.register_model("m", str(p2), {"accuracy": 0.7}, "h2", version="0.1.1")
    with pytest.raises(ValueError):
        registry.set_active_version("m", "0.1.1")


def test_rollback_model_restores_previous(tmp_path, registry):
    p1 = tmp_path / "p1.bin"
    p1.write_text("1")
    registry.register_model("m2", str(p1), {"accuracy": 0.9}, "h1", version="0.1.0")
    registry.set_active_version("m2", "0.1.0")
    p2 = tmp_path / "p2.bin"
    p2.write_text("2")
    registry.register_model("m2", str(p2), {"accuracy": 0.92}, "h2", version="0.1.1")
    registry.set_active_version("m2", "0.1.1")
    registry.rollback_model("m2")
    active = registry.get_model("m2", active_only=True)
    assert active.version == "0.1.0"

