import types
import importlib
import importlib.util
from pathlib import Path
import sys

if "services.resilience" not in sys.modules:
    sys.modules["services.resilience"] = types.ModuleType("services.resilience")
if "services.resilience.metrics" not in sys.modules:
    metrics_stub = types.ModuleType("services.resilience.metrics")
    metrics_stub.circuit_breaker_state = types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    )
    sys.modules["services.resilience.metrics"] = metrics_stub

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
    path = Path(__file__).resolve().parents[2] / "models" / "ml" / "model_registry.py"
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


def test_download_artifact_file_scheme(tmp_path, registry):
    src = tmp_path / "src.bin"
    src.write_text("data")
    dest = tmp_path / "dest.bin"
    registry.download_artifact(f"file://{src}", str(dest))
    assert dest.read_text() == "data"


def test_download_artifact_local_path(tmp_path, registry):
    src = tmp_path / "src2.bin"
    src.write_text("info")
    dest = tmp_path / "dest2.bin"
    registry.download_artifact(str(src), str(dest))
    assert dest.read_text() == "info"


def test_download_artifact_http(monkeypatch, tmp_path, registry):
    class DummyResponse:
        def __init__(self, data: bytes) -> None:
            self._data = data

        def raise_for_status(self) -> None:
            pass

        def iter_content(self, chunk_size: int = 8192):
            yield self._data

    requests_mod = registry.download_artifact.__globals__["requests"]
    monkeypatch.setattr(
        requests_mod, "get", lambda url, stream=True: DummyResponse(b"xyz")
    )
    dest = tmp_path / "dest3.bin"
    registry.download_artifact("http://example.com/file.bin", str(dest))
    assert dest.read_text() == "xyz"


def test_download_artifact_invalid_scheme(tmp_path, registry):
    with pytest.raises(ValueError):
        registry.download_artifact("ftp://host/file.bin", str(tmp_path / "x"))
