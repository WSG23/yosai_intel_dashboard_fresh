import json
from pathlib import Path

import pandas as pd
from sklearn.linear_model import LogisticRegression

from yosai_intel_dashboard.src.models.ml.training.bias import detect_bias
from yosai_intel_dashboard.src.models.ml.training import pipeline as train_pipeline


class DummyRegistry:
    def get_model(self, *args, **kwargs):
        return None

    def _metrics_improved(self, *args, **kwargs):
        return True

    class _Rec:
        def __init__(self):
            self.version = "0.1.0"
            self.metrics = {}

    def register_model(self, *args, **kwargs):
        return self._Rec()

    def set_active_version(self, *args, **kwargs):
        pass


def test_detect_bias_returns_metrics():
    y_true = [0, 1, 0, 1]
    y_pred = [0, 1, 1, 0]
    sensitive = ["A", "A", "B", "B"]
    metrics = detect_bias(y_true, y_pred, sensitive)
    assert "overall" in metrics and "by_group" in metrics


def test_pipeline_bias_reporting(tmp_path, monkeypatch):
    monkeypatch.setattr(train_pipeline, "preprocess_events", lambda df: df)
    df = pd.DataFrame(
        {
            "feat": [0, 1, 0, 1],
            "sensitive": ["A", "A", "B", "B"],
            "target": [0, 1, 0, 1],
        }
    )
    models = {"lr": (LogisticRegression(max_iter=100), {})}
    registry = DummyRegistry()
    tp = train_pipeline.TrainingPipeline(registry=registry, cv_splits=2)
    report = tmp_path / "bias.json"
    res = tp.run(
        df,
        target_column="target",
        models=models,
        bias_column="sensitive",
        bias_report=report,
    )
    assert res.bias_metrics and "overall" in res.bias_metrics
    assert report.exists() and json.loads(report.read_text()) == res.bias_metrics
