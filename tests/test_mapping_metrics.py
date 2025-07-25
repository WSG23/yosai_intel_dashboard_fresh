import pandas as pd
from core import performance
import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location(
    "ai_processor",
    Path(__file__).resolve().parents[1] / "mapping" / "processors" / "ai_processor.py",
)
ai_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ai_module)
AIColumnMapperAdapter = ai_module.AIColumnMapperAdapter
from mapping.metrics import get_mapping_accuracy_summary


class DummyAdapter:
    def get_ai_column_suggestions(self, df, filename):
        return {c: {"field": c.lower(), "confidence": 0.5} for c in df.columns}

    def save_verified_mappings(self, filename, mapping, metadata):
        return True


def test_mapping_metrics_recorded(monkeypatch):
    monitor = performance.PerformanceMonitor(max_metrics=10)
    monkeypatch.setattr(performance, "_performance_monitor", monitor)

    df = pd.DataFrame({"A": [1]})
    adapter = AIColumnMapperAdapter(DummyAdapter())
    adapter.suggest(df, "file.csv")

    summary = get_mapping_accuracy_summary()
    assert summary["count"] == 1
    assert summary["mean"] == 0.5
