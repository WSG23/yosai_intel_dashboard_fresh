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
def registry(monkeypatch):
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
    return mr.ModelRegistry("sqlite:///:memory:", bucket="bucket", s3_client=DummyS3())


def test_log_explanation_persists(registry):
    registry.log_explanation("pred1", "model", "1.0", {"shap_values": [1, 2]})
    rec = registry.get_explanation("pred1")
    assert rec["model_name"] == "model"
    assert rec["explanation"]["shap_values"] == [1, 2]
