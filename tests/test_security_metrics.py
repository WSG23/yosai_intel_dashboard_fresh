import pandas as pd
import pytest

from services.analytics.security_metrics import SecurityMetrics
from services.analytics.security_patterns import SecurityPatternsAnalyzer


def test_security_metrics_validation():
    ts = pd.Timestamp.utcnow().to_pydatetime()
    m = SecurityMetrics(90, "low", (85, 95), "test", ts)
    assert m.score == 90
    with pytest.raises(ValueError):
        SecurityMetrics(110, "low", (80, 90), "m", ts)
    with pytest.raises(ValueError):
        SecurityMetrics(90, "bad", (80, 90), "m", ts)
    with pytest.raises(ValueError):
        SecurityMetrics(90, "low", (90, 80), "m", ts)
    with pytest.raises(ValueError):
        SecurityMetrics(90, "low", (80, 90), "", ts)
    with pytest.raises(ValueError):
        SecurityMetrics(90, "low", (80, 90), "test", "bad")


def test_security_score_returns_metrics():
    analyzer = SecurityPatternsAnalyzer()
    df = pd.DataFrame(
        {
            "event_id": [1, 2, 3, 4],
            "timestamp": [
                "2024-01-01 10:00:00",
                "2024-01-01 11:00:00",
                "2024-01-01 23:00:00",
                "2024-01-02 02:00:00",
            ],
            "person_id": ["u1", "u2", "u3", "u4"],
            "door_id": ["d1", "d1", "d2", "d2"],
            "access_result": ["Granted", "Denied", "Denied", "Granted"],
            "badge_status": ["Valid", "Invalid", "Valid", "Valid"],
        }
    )
    df = analyzer._prepare_data(df)
    metrics = analyzer._calculate_security_score(df)
    assert isinstance(metrics, SecurityMetrics)
    assert 0 <= metrics.score <= 100
