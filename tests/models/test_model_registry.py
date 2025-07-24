import types
import importlib
import importlib.util
from pathlib import Path

import pytest

from sqlalchemy.orm import Session as SASession


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
def registry(monkeypatch, stub_services_registry):
    path = (
        Path(__file__).resolve().parents[2]
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


@pytest.fixture
def track_session_closes(monkeypatch):
    calls = []
    original = SASession.close

    def patched(self):
        calls.append(True)
        original(self)

    monkeypatch.setattr(SASession, "close", patched)
    return calls


def test_register_model_closes_session(tmp_path, registry, track_session_closes):
    path = tmp_path / "model.bin"
    path.write_text("x")
    registry.register_model("m", str(path), {"acc": 1.0}, "hash")
    assert len(track_session_closes) >= 2


def test_get_model_closes_session(tmp_path, registry, track_session_closes):
    path = tmp_path / "model2.bin"
    path.write_text("y")
    model = registry.register_model("m2", str(path), {"acc": 1.0}, "hash")
    track_session_closes.clear()
    registry.get_model("m2", version=model.version)
    assert len(track_session_closes) >= 1


def test_list_models_closes_session(registry, track_session_closes):
    registry.list_models()
    assert len(track_session_closes) >= 1


def test_delete_model_closes_session(tmp_path, registry, track_session_closes):
    path = tmp_path / "model3.bin"
    path.write_text("z")
    model = registry.register_model("m3", str(path), {"acc": 1.0}, "hash")
    track_session_closes.clear()
    registry.delete_model(model.id)
    assert len(track_session_closes) >= 1


def test_set_active_version_closes_session(tmp_path, registry, track_session_closes):
    path = tmp_path / "model4.bin"
    path.write_text("w")
    model = registry.register_model("m4", str(path), {"acc": 1.0}, "hash")
    track_session_closes.clear()
    registry.set_active_version("m4", model.version)
    assert len(track_session_closes) >= 1

