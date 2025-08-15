import json
from types import SimpleNamespace

import pytest

from intel_analysis_service.ml.model_registry import ModelRegistry


def test_model_round_trip(tmp_path):
    reg = ModelRegistry(tmp_path)
    model = SimpleNamespace(value=1)
    params = {"a": 1}
    meta = reg.save_model("dummy", model, params, version="v1")
    loaded_model, loaded_meta = reg.load_model("dummy", meta.version)
    assert loaded_model.value == model.value
    assert loaded_meta.sha256 == meta.sha256


def test_corrupted_model_file(tmp_path):
    reg = ModelRegistry(tmp_path)
    model = SimpleNamespace(value=1)
    meta = reg.save_model("dummy", model, {}, version="v1")
    model_path = tmp_path / "dummy" / meta.version / "model.pkl"
    model_path.write_bytes(b"corrupted")
    with pytest.raises(ValueError):
        reg.load_model("dummy", meta.version)


def test_corrupted_metadata_hash(tmp_path):
    reg = ModelRegistry(tmp_path)
    model = SimpleNamespace(value=1)
    meta = reg.save_model("dummy", model, {}, version="v1")
    metadata_path = tmp_path / "dummy" / meta.version / "metadata.json"
    data = json.loads(metadata_path.read_text())
    data["sha256"] = "0" * 64
    metadata_path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        reg.load_model("dummy", meta.version)
