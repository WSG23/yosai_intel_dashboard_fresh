"""Additional tests for vectorized functions."""

import pandas as pd

from yosai_intel_dashboard.src.services.analytics.anomaly_detection import AnomalyDetector
from yosai_intel_dashboard.src.services.analytics.security_patterns import SecurityPatternsAnalyzer


class TestVectorizedFunctionsFixed:
    """Fixed tests for vectorized functions"""

    def test_extract_failure_patterns_vectorized(self):
        """Test failure pattern extraction"""
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
        patterns = analyzer._detect_statistical_threats(df)
        assert isinstance(patterns, list)

    def test_anomaly_detection_with_new_class(self):
        """Test anomaly detection with corrected class name"""
        detector = AnomalyDetector()

        df = pd.DataFrame(
            {
                "event_id": range(15),
                "timestamp": pd.date_range(
                    "2024-01-01 08:00:00", periods=15, freq="3min"
                ),
                "person_id": ["u1"] * 12 + ["u2", "u2", "u2"],
                "door_id": ["d1"] * 15,
                "access_result": ["Granted"] * 15,
            }
        )

        df = detector._prepare_anomaly_data(df)
        anomalies = detector._detect_frequency_anomalies(df)
        assert isinstance(anomalies, list)
