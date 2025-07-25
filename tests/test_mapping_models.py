import pandas as pd
import tempfile
import yaml

from mapping.models import load_model, RuleBasedModel
from mapping.models.base import MappingModel
from yosai_intel_dashboard.src.core.performance import PerformanceMonitor


def test_load_model_from_yaml(tmp_path):
    config = {
        "type": "rule_based",
        "params": {"mappings": {"A": "timestamp"}},
    }
    path = tmp_path / "model.yaml"
    path.write_text(yaml.safe_dump(config))

    model = load_model(str(path))
    assert isinstance(model, MappingModel)
    df = pd.DataFrame({"A": [1]})
    out = model.cached_suggest(df, "f.csv")
    assert out["A"]["field"] == "timestamp"



def test_model_caching_and_metrics(monkeypatch):
    monitor = PerformanceMonitor(max_metrics=10)
    from yosai_intel_dashboard.src.core import performance as perf_module

    monkeypatch.setattr(perf_module, "_performance_monitor", monitor)
    model = RuleBasedModel({"A": "timestamp"})

    df = pd.DataFrame({"A": [1]})
    model.cached_suggest(df, "x.csv")
    model.cached_suggest(df, "x.csv")
    metrics = [m.name for m in monitor.metrics]
    assert "mapping.suggest.latency" in metrics
    assert "mapping.suggest.accuracy" in metrics
