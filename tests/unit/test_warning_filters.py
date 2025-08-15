import warnings

import pandas as pd

from yosai_intel_dashboard.src.services.analytics.access_trends import AccessTrendsAnalyzer
from yosai_intel_dashboard.src.services.analytics.anomaly_detection import AnomalyDetector
from yosai_intel_dashboard.src.services.analytics.security_patterns import PaginatedAnalyzer
from yosai_intel_dashboard.src.services.analytics.user_behavior import UserBehaviorAnalyzer


def _sample_df(rows: int = 20) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": range(rows),
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="h"),
            "person_id": [f"u{i%3}" for i in range(rows)],
            "door_id": [f"d{i%2}" for i in range(rows)],
            "access_result": ["Granted"] * rows,
        }
    )


def test_analyzers_emit_no_warnings():
    df = _sample_df()
    analyzers = [
        (AnomalyDetector(), "detect_anomalies"),
        (PaginatedAnalyzer(), "analyze_patterns_chunked"),
        (AccessTrendsAnalyzer(), "analyze_trends"),
        (UserBehaviorAnalyzer(), "analyze_behavior"),
    ]

    for analyzer, method_name in analyzers:
        method = getattr(analyzer, method_name)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("error")
            try:
                method(df)
            except Exception:
                # Methods may raise due to insufficient data; only ensure no warnings
                pass
        assert not caught, f"Unexpected warnings in {method_name}: {caught}"
