from __future__ import annotations

import json
import sys
import types
from pathlib import Path
from tests.import_helpers import safe_import, import_optional

if "services.resilience" not in sys.modules:
    safe_import('services.resilience', types.ModuleType("services.resilience"))
if "services.resilience.metrics" not in sys.modules:
    metrics_stub = types.ModuleType("services.resilience.metrics")
    metrics_stub.circuit_breaker_state = types.SimpleNamespace(
        labels=lambda *a, **k: types.SimpleNamespace(inc=lambda *a, **k: None)
    )
    safe_import('services.resilience.metrics', metrics_stub)

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

FEATURE_DEF = {"features": ["hour", "day_of_week", "user_event_count"]}


class DummyStore:
    def get_training_dataframe(self, service, entity_df):
        return entity_df.assign(dummy=1)

    def get_online_features(self, service, entity_rows):
        return {"dummy": [1 for _ in entity_rows]}


class DummyS3:
    def upload_file(self, src, bucket, key):
        pass

    def download_file(self, bucket, key, dest):
        Path(dest).write_text("")


def test_load_definitions(tmp_path):
    path = tmp_path / "defs.yaml"
    path.write_text(json.dumps(FEATURE_DEF))
    from yosai_intel_dashboard.models.ml.feature_pipeline import FeaturePipeline

    pipe = FeaturePipeline(path)
    pipe.load_definitions()
    assert pipe.feature_list == FEATURE_DEF["features"]


def test_fit_transform(tmp_path):
    path = tmp_path / "defs.json"
    path.write_text(json.dumps(FEATURE_DEF))
    from yosai_intel_dashboard.models.ml.feature_pipeline import FeaturePipeline

    data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="H"),
            "person_id": ["u1", "u2", "u3"],
            "door_id": ["d1", "d1", "d2"],
            "access_result": ["Granted", "Denied", "Granted"],
        }
    )

    pipe = FeaturePipeline(path)
    pipe.load_definitions()
    pipe.register_transformer("scale", StandardScaler(), ["user_event_count"])
    transformed = pipe.fit_transform(data)
    assert "hour" in transformed.columns
    assert "user_event_count" in transformed.columns


def test_batch_online(tmp_path):
    path = tmp_path / "defs.json"
    path.write_text(json.dumps(FEATURE_DEF))
    from yosai_intel_dashboard.models.ml.feature_pipeline import FeaturePipeline

    store = DummyStore()
    pipe = FeaturePipeline(path, feature_store=store)
    entity_df = pd.DataFrame({"person_id": ["u1"], "event_timestamp": ["2024-01-01"]})
    batch = pipe.compute_batch_features(None, entity_df)
    online = pipe.compute_online_features(None, [{"person_id": "u1"}])
    assert "dummy" in batch.columns
    assert online["dummy"] == [1]


def test_importance_and_drift(tmp_path):
    path = tmp_path / "defs.json"
    path.write_text(json.dumps(FEATURE_DEF))
    from yosai_intel_dashboard.models.ml.feature_pipeline import FeaturePipeline

    data = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=10, freq="H"),
            "person_id": ["u1"] * 10,
            "door_id": ["d1"] * 10,
            "access_result": ["Granted"] * 10,
        }
    )
    labels = [0, 1] * 5
    pipe = FeaturePipeline(path)
    pipe.load_definitions()
    X = pipe.fit_transform(data)
    model = LogisticRegression().fit(X, labels)
    imp = pipe.feature_importance(model, X, pd.Series(labels))
    assert not imp.empty
    drift = pipe.detect_drift(X, X + 1, threshold=0.5)
    assert drift


def test_versioning_and_rollback(tmp_path):
    path = tmp_path / "defs.json"
    path.write_text(json.dumps(FEATURE_DEF))
    from yosai_intel_dashboard.models.ml.feature_pipeline import FeaturePipeline
    from yosai_intel_dashboard.models.ml.model_registry import ModelRegistry

    registry = ModelRegistry("sqlite:///:memory:", bucket="b", s3_client=DummyS3())
    pipe = FeaturePipeline(path, registry=registry)
    ver = pipe.register_version("m", "m.joblib", {"acc": 1.0}, "hash")
    assert ver
    pipe.rollback("m", ver)
    assert pipe.version == ver
