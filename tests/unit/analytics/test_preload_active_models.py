from types import SimpleNamespace
from pathlib import Path
import sys
import os
from typing import Any

os.environ.setdefault("LIGHTWEIGHT_SERVICES", "1")


class _FakeJoblib:
    def dump(self, obj, path):
        Path(path).write_text("data")

    def load(self, path):
        return {"x": 1}


sys.modules.setdefault("joblib", _FakeJoblib())

from yosai_intel_dashboard.src.services.common.analytics_utils import (
    preload_active_models,
)


class DummyRegistry:
    def __init__(self, tmp_path: Path) -> None:
        self._tmp = tmp_path
        self._records = [SimpleNamespace(name="demo", storage_uri="remote/model.bin", version="1")]

    def list_models(self):
        return self._records

    def get_model(self, name, active_only=True):
        return self._records[0]

    def download_artifact(self, uri, dest):
        Path(dest).write_text("data")


def test_preload_active_models_loads(tmp_path):
    service = SimpleNamespace(model_registry=DummyRegistry(tmp_path), model_dir=tmp_path)
    preload_active_models(service)
    assert service.models["demo"] == {"x": 1}
    assert (tmp_path / "demo" / "1" / "model.bin").exists()


class MicroService:
    def __init__(self, tmp_path: Path) -> None:
        self.model_registry = DummyRegistry(tmp_path)
        self.model_dir = tmp_path
        self.models: dict[str, Any] = {}

    def preload_active_models(self) -> None:
        preload_active_models(self)


class SyncService:
    def __init__(self, tmp_path: Path) -> None:
        self.model_registry = DummyRegistry(tmp_path)
        self.model_dir = tmp_path
        self.models: dict[str, Any] = {}

    def preload_active_models(self) -> None:
        preload_active_models(self)


def test_microservice_preload_active_models(tmp_path):
    svc = MicroService(tmp_path)
    svc.preload_active_models()
    assert svc.models["demo"] == {"x": 1}


def test_service_preload_active_models(tmp_path):
    svc = SyncService(tmp_path)
    svc.preload_active_models()
    assert svc.models["demo"] == {"x": 1}
