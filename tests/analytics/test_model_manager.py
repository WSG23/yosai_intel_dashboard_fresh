from types import SimpleNamespace
from pathlib import Path

from yosai_intel_dashboard.src.services.helpers.model_manager import ModelManager


class DummyRegistry:
    def __init__(self):
        self.download_called = False
        self.store_called = False

    def get_model(self, name, active_only=True):
        return SimpleNamespace(storage_uri="remote/model.bin", version="1")

    def get_version_metadata(self, name):
        return None

    def download_artifact(self, uri, dest):
        self.download_called = True
        Path(dest).write_text("data")

    def store_version_metadata(self, name, version):
        self.store_called = True


def test_model_manager_downloads(tmp_path):
    registry = DummyRegistry()
    config = SimpleNamespace(analytics=SimpleNamespace(ml_models_path=str(tmp_path)))
    manager = ModelManager(registry, config)
    path = manager.load_model("dummy")
    assert registry.download_called
    assert registry.store_called
    assert path is not None
    assert Path(path).exists()


def test_model_manager_uses_cache(tmp_path):
    registry = DummyRegistry()
    registry.get_version_metadata = lambda name: "1"
    config = SimpleNamespace(analytics=SimpleNamespace(ml_models_path=str(tmp_path)))
    expected = Path(tmp_path) / "dummy" / "1" / "model.bin"
    expected.parent.mkdir(parents=True)
    expected.write_text("data")
    manager = ModelManager(registry, config)
    path = manager.load_model("dummy")
    assert path == str(expected)
    assert not registry.download_called
