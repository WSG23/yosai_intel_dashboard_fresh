import pandas as pd

from analytics.security_patterns.data_prep import prepare_security_data
from analytics.security_patterns.statistical_detection import (
    detect_failure_rate_anomalies,
)


def test_prepare_security_data_basic():
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 10:00:00"],
            "person_id": ["u1"],
            "door_id": ["d1"],
            "access_result": ["Granted"],
        }
    )
    cleaned = prepare_security_data(df)
    assert "hour" in cleaned.columns
    assert cleaned["access_granted"].iloc[0] == 1


def test_detect_failure_rate_anomalies():
    rows = []
    for i in range(6):
        rows.append(
            {
                "timestamp": f"2024-01-01 09:{i:02d}:00",
                "person_id": "bad",
                "door_id": "d1",
                "access_result": "Denied",
            }
        )
    for i in range(6):
        rows.append(
            {
                "timestamp": f"2024-01-01 10:{i:02d}:00",
                "person_id": f"ok{i}",
                "door_id": "d1",
                "access_result": "Granted",
            }
        )
    df = pd.DataFrame(rows)
    cleaned = prepare_security_data(df)
    threats = detect_failure_rate_anomalies(cleaned)
    assert threats
    indicator = threats[0]
    assert indicator.threat_type == "unusual_failure_rate"
    assert indicator.severity == "critical"


def test_failure_rate_anomalies_none():
    rows = []
    for i in range(6):
        rows.append(
            {
                "timestamp": f"2024-01-01 09:{i:02d}:00",
                "person_id": "u1",
                "door_id": "d1",
                "access_result": "Granted",
            }
        )
    for i in range(6):
        rows.append(
            {
                "timestamp": f"2024-01-01 10:{i:02d}:00",
                "person_id": "u2",
                "door_id": "d1",
                "access_result": "Granted",
            }
        )
    df = pd.DataFrame(rows)
    cleaned = prepare_security_data(df)
    threats = detect_failure_rate_anomalies(cleaned)
    assert threats == []
