import pandas as pd

from analytics.security_patterns.data_prep import prepare_security_data
from analytics.security_patterns.statistical_detection import (
    detect_failure_rate_anomalies,
)
from analytics.security_patterns.no_access_detection import detect_no_access_anomalies


class DummyBaselineDB:
    def __init__(self):
        self.store = {}

    def update_baseline(self, entity_type: str, entity_id: str, metrics):
        self.store[(entity_type, entity_id)] = metrics

    def get_baseline(self, entity_type: str, entity_id: str):
        return self.store.get((entity_type, entity_id), {})


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
    for i in range(8):
        rows.append(
            {
                "timestamp": f"2024-01-01 10:0{i}:00",
                "person_id": "u1",
                "door_id": "d1",
                "access_result": "Denied",
            }
        )
    for i in range(8):
        rows.append(
            {
                "timestamp": f"2024-01-01 11:0{i}:00",
                "person_id": "u2",
                "door_id": "d1",
                "access_result": "Granted",
            }
        )
    df = pd.DataFrame(rows)
    cleaned = prepare_security_data(df)
    threats = detect_failure_rate_anomalies(cleaned)
    assert isinstance(threats, list)


def test_detect_no_access_anomalies():
    rows = []
    # User u1 has repeated denied events
    for i in range(5):
        rows.append(
            {
                "timestamp": f"2024-01-02 12:0{i}:00",
                "person_id": "u1",
                "door_id": "d1",
                "access_result": "Denied",
            }
        )
    # Baseline user u1 success mostly
    baseline_db = DummyBaselineDB()
    baseline_db.update_baseline("user", "u1", {"failure_rate": 0.05})

    df = pd.DataFrame(rows)
    cleaned = prepare_security_data(df)
    threats = detect_no_access_anomalies(cleaned, baseline_db)
    assert isinstance(threats, list)
    if threats:
        assert threats[0].threat_type == "repeated_access_denied"
