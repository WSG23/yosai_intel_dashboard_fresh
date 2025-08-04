import importlib.util
import pathlib
import shutil
import sys
import types
from pathlib import Path

import joblib
import pytest
from yosai_intel_dashboard.src.core.imports.resolver import safe_import

# Load ModelABTester directly to avoid heavy service imports
services_path = pathlib.Path(__file__).resolve().parents[1] / "services"
stub_pkg = types.ModuleType("services")
stub_pkg.__path__ = [str(services_path)]
safe_import('services', stub_pkg)

ab_path = services_path / "ab_testing.py"
spec = importlib.util.spec_from_file_location("services.ab_testing", ab_path)
ab_testing = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ab_testing)  # type: ignore
ModelABTester = ab_testing.ModelABTester


class DummyRegistry:
    """Minimal registry returning local artifacts."""

    def __init__(self, artifacts):
        self.artifacts = artifacts

    def get_model(self, name, version=None, active_only=False):
        path = self.artifacts.get(version)
        if path is None:
            return None
        return types.SimpleNamespace(storage_uri=str(path))

    def download_artifact(self, storage_uri, destination):
        shutil.copy(storage_uri, destination)


def _make_model(path: Path, value: str) -> None:
    class StubModel:
        def __init__(self, v):
            self.v = v

        def predict(self, data):
            return [self.v for _ in data]

    joblib.dump(StubModel(value), path)


def test_predict_routes_by_weights(tmp_path):
    m1 = tmp_path / "m1.joblib"
    m2 = tmp_path / "m2.joblib"
    _make_model(m1, "one")
    _make_model(m2, "two")
    registry = DummyRegistry({"1": m1, "2": m2})

    tester = ModelABTester(
        "model",
        registry,
        weights={"1": 1.0, "2": 0.0},
        weights_file=tmp_path / "w.json",
        model_dir=tmp_path / "models",
    )
    result = tester.predict([0, 1])
    assert result == ["one", "one"]

    tester.set_weights({"1": 0.0, "2": 1.0})
    result = tester.predict([0])
    assert result == ["two"]


def test_predict_missing_or_invalid_model(tmp_path):
    bad = tmp_path / "bad.joblib"
    bad.write_text("not a pickle")
    registry = DummyRegistry({"1": bad})
    tester = ModelABTester(
        "model",
        registry,
        weights={"1": 1.0},
        weights_file=tmp_path / "w.json",
        model_dir=tmp_path / "models",
    )
    with pytest.raises(RuntimeError, match="Model version 1 not loaded"):
        tester.predict([1])
