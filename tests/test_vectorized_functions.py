import pandas as pd

from services.analytics.anomaly_detection import AnomalyDetector
from services.analytics.security_patterns import SecurityPatternsAnalyzer


def test_extract_failure_patterns_vectorized():
    analyzer = SecurityPatternsAnalyzer()
    df = pd.DataFrame(
        {
            "event_id": range(6),
            "timestamp": pd.date_range("2024-01-01", periods=6, freq="H"),
            "person_id": ["u1", "u1", "u1", "u2", "u3", "u1"],
            "door_id": ["d1"] * 6,
            "access_result": ["Denied"] * 6,
        }
    )
    df = analyzer._prepare_data(df)
    patterns = analyzer._extract_failure_patterns(df)
    assert patterns == [
        {"type": "repeated_failures", "user": "u1", "count": 4, "severity": "high"}
    ]


def test_identify_timing_patterns_vectorized():
    analyzer = SecurityPatternsAnalyzer()
    df = pd.DataFrame(
        {
            "event_id": range(5),
            "timestamp": pd.date_range("2024-01-01 20:00:00", periods=5, freq="H"),
            "person_id": ["u1"] * 5,
            "door_id": ["d1"] * 5,
            "access_result": ["Granted"] * 5,
        }
    )
    df = analyzer._prepare_data(df)
    patterns = analyzer._identify_timing_patterns(df)
    assert patterns == [{"type": "frequent_after_hours", "user": "u1", "count": 5}]


def test_detect_frequency_anomalies_vectorized():
    detector = AnomalyDetector()
    df = pd.DataFrame(
        {
            "event_id": range(15),
            "timestamp": pd.date_range("2024-01-01 08:00:00", periods=15, freq="3min"),
            "person_id": ["u1"] * 12 + ["u2", "u2", "u2"],
            "door_id": ["d1"] * 15,
            "access_result": ["Granted"] * 15,
        }
    )
    df = detector._prepare_data(df)
    anomalies = detector._detect_frequency_anomalies(df)
    assert any(
        a["type"] == "activity_burst" and a["user_id"] == "u1" for a in anomalies
    )
