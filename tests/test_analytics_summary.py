import pandas as pd

from yosai_intel_dashboard.src.services.analytics_summary import (
    generate_basic_analytics,
    generate_sample_analytics,
)


def test_generate_basic_analytics():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "x"]})
    result = generate_basic_analytics(df)
    assert result["total_events"] == 3
    assert result["summary"]["a"]["mean"] == 2.0
    assert result["summary"]["b"]["type"] == "categorical"


def test_generate_sample_analytics():
    result = generate_sample_analytics()
    assert result["status"] == "success"
    assert result["total_events"] > 0
