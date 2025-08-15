import importlib.util
import types
from pathlib import Path
import os

import pytest

os.environ.setdefault("CACHE_TTL", "1")


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
    mr = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(mr)
    monkeypatch.setattr(mr, "mlflow", DummyMlflow())
    return mr.ModelRegistry(
        f"sqlite:///{tmp_path}/db.sqlite",
        bucket="bucket",
        s3_client=DummyS3(),
        metric_thresholds={"acc": 0.05},
    )


def test_version_bumping(monkeypatch, tmp_path, registry):
    p1 = tmp_path / "m1.bin"
    p1.write_text("a")
    r1 = registry.register_model("m", str(p1), {"acc": 0.8}, "h1")
    assert r1.version == "0.1.0"
    registry.set_active_version("m", r1.version)

    p2 = tmp_path / "m2.bin"
    p2.write_text("b")
    r2 = registry.register_model("m", str(p2), {"acc": 0.86}, "h2")
    assert r2.version == "0.2.0"
    registry.set_active_version("m", r2.version)

    p3 = tmp_path / "m3.bin"
    p3.write_text("c")
    r3 = registry.register_model("m", str(p3), {"acc": 0.84}, "h3")
    assert r3.version == "0.2.1"
