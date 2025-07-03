import pandas as pd
from analytics.security_patterns import SecurityPatternsAnalyzer


def test_analyze_failed_access_returns_expected_keys():
    analyzer = SecurityPatternsAnalyzer()
    df = pd.DataFrame(
        {
            "event_id": [1, 2, 3, 4, 5],
            "timestamp": pd.date_range("2024-01-01 08:00:00", periods=5, freq="H"),
            "person_id": ["u1", "u1", "u2", "u1", "u3"],
            "door_id": ["d1", "d2", "d2", "d1", "d1"],
            "access_result": ["Denied"] * 5,
        }
    )
    prepared = analyzer._prepare_data(df)
    result = analyzer._analyze_failed_access(prepared)
    expected_keys = {
        "total",
        "failure_rate",
        "high_risk_users",
        "peak_failure_times",
        "top_failure_doors",
        "patterns",
        "risk_level",
    }
    assert set(result.keys()) == expected_keys
