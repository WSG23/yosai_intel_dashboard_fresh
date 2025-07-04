import pandas as pd
from sklearn.ensemble import IsolationForest

from analytics.anomaly_detection.data_prep import prepare_anomaly_data
from analytics.anomaly_detection.ml_inference import detect_ml_anomalies


def test_prepare_anomaly_data_basic():
    df = pd.DataFrame({
        "timestamp": ["2024-01-01 00:00:00"],
        "person_id": ["u1"],
        "door_id": ["d1"],
        "access_result": ["Granted"],
    })
    cleaned = prepare_anomaly_data(df)
    assert "hour" in cleaned.columns
    assert cleaned["access_granted"].iloc[0] == 1


def test_detect_ml_anomalies_runs():
    df = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=20, freq="min"),
        "person_id": ["u1"] * 20,
        "door_id": ["d1"] * 20,
        "access_result": ["Granted"] * 20,
    })
    cleaned = prepare_anomaly_data(df)
    model = IsolationForest(random_state=42, n_estimators=10, contamination=0.1)
    anomalies = detect_ml_anomalies(cleaned, 0.9, model)
    assert isinstance(anomalies, list)
