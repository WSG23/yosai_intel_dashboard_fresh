import importlib
import importlib.util
import sys
import types
from pathlib import Path
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

if "services.resilience" not in sys.modules:
    safe_import('services.resilience', types.ModuleType("services.resilience"))
if "services.resilience.metrics" not in sys.modules:
    metrics_stub = types.ModuleType("services.resilience.metrics")
    metrics_stub.circuit_breaker_state = types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    )
    safe_import('services.resilience.metrics', metrics_stub)

import pandas as pd
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


def test_rollback_model_closes_session(tmp_path, registry, track_session_closes):
    p1 = tmp_path / "m1.bin"
    p1.write_text("a")
    registry.register_model("m5", str(p1), {"acc": 1.0}, "h1", version="0.1.0")
    registry.set_active_version("m5", "0.1.0")
    p2 = tmp_path / "m2.bin"
    p2.write_text("b")
    registry.register_model("m5", str(p2), {"acc": 0.9}, "h2", version="0.1.1")
    registry.set_active_version("m5", "0.1.1")
    track_session_closes.clear()
    registry.rollback_model("m5")
    calls = len(track_session_closes)
    active = registry.get_model("m5", active_only=True)
    assert calls >= 1
    assert active.version == "0.1.0"


def test_register_model_prunes_versions(tmp_path, registry):
    for i in range(6):
        p = tmp_path / f"p{i}.bin"
        p.write_text(str(i))
        registry.register_model(
            "prune", str(p), {"acc": 1.0}, f"h{i}", version=f"0.1.{i}"
        )
    records = registry.list_models("prune")
    assert len(records) == 5
    versions = {r.version for r in records}
    assert "0.1.0" not in versions


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
        requests_mod,
        "get",
        lambda url, stream=True: DummyResponse(b"xyz"),
        raising=False,
    )
    dest = tmp_path / "dest3.bin"
    registry.download_artifact("http://example.com/file.bin", str(dest))
    assert dest.read_text() == "xyz"


def test_download_artifact_invalid_scheme(tmp_path, registry):
    with pytest.raises(ValueError):
        registry.download_artifact("ftp://host/file.bin", str(tmp_path / "x"))


def test_version_metadata(tmp_path, registry, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry.store_version_metadata("demo", "1.2.3")
    assert registry.get_version_metadata("demo") == "1.2.3"


@pytest.mark.skip(reason="requires full analytics stack")
def test_log_features_and_drift(monkeypatch, stub_services_registry):
    # Provide minimal stubs so mlflow import succeeds
    stub_req = types.ModuleType("requests")
    adapters_mod = types.ModuleType("requests.adapters")

    class HTTPAdapter:  # minimal stub
        pass

    adapters_mod.HTTPAdapter = HTTPAdapter
    stub_req.adapters = adapters_mod
    stub_req.exceptions = types.ModuleType("requests.exceptions")
    class Response:  # minimal stub for dependencies
        pass
    stub_req.Response = Response
    safe_import('requests', stub_req)
    safe_import('requests.adapters', adapters_mod)
    safe_import('requests.exceptions', stub_req.exceptions)

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
    mlflow_stub.set_tracking_uri = lambda *a, **k: None
    safe_import('mlflow', mlflow_stub)

    services_pkg = types.ModuleType("services")
    services_pkg.__path__ = [str(Path(__file__).resolve().parents[2] / "services")]
    safe_import('services', services_pkg)
    registry_mod = types.ModuleType("core.registry")
    registry_mod.get_service = lambda name: None
    safe_import('core.registry', registry_mod)

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
    registry = mr.ModelRegistry(
        "sqlite:///:memory:", bucket="bucket", s3_client=DummyS3()
    )

    df1 = pd.DataFrame({"a": [0, 1, 0, 1]})
    df2 = pd.DataFrame({"a": [1, 1, 1, 1]})
    registry.log_features("demo", df1)
    registry.log_features("demo", df2)
    metrics = registry.get_drift_metrics("demo")
    assert metrics["a"] > 0
