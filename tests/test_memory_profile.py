import importlib.util

import pandas as pd

spec = importlib.util.spec_from_file_location(
    "unique_patterns_analyzer", "analytics/unique_patterns_analyzer.py"
)
upa = importlib.util.module_from_spec(spec)
spec.loader.exec_module(upa)


def test_prepare_data_memory_usage():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=1000, freq="h"),
            "door_id": ["x"] * 1000,
        }
    )
    base = df.memory_usage(deep=True).sum()
    prepared = upa.UniquePatternAnalyzer()._prepare_data(df)
    diff = prepared.memory_usage(deep=True).sum() - base
    assert diff < 200_000
