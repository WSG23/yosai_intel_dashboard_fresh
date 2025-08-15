import importlib.util
from pathlib import Path

import pandas as pd

FEATURE_PATH = (
    Path(__file__).resolve().parents[1] / "analytics" / "feature_extraction.py"
)
spec = importlib.util.spec_from_file_location("feature_extraction", FEATURE_PATH)
feature_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(feature_mod)
extract_event_features = feature_mod.extract_event_features


def test_extract_event_features_basic():
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01 23:00:00", "2024-01-02 09:00:00"],
            "person_id": ["u1", "u2"],
            "door_id": ["d1", "d1"],
            "access_result": ["Denied", "Granted"],
        }
    )
    features = extract_event_features(df)
    assert "hour" in features.columns
    assert features.loc[0, "is_after_hours"]
    assert features.loc[1, "access_granted"] == 1
    assert features.loc[0, "door_event_count"] == 2


def test_extract_event_features_counts():
    df = pd.DataFrame(
        {
            "timestamp": pd.date_range("2024-01-01", periods=3, freq="H"),
            "person_id": ["u1", "u1", "u2"],
            "door_id": ["d1", "d1", "d2"],
            "access_result": ["Granted", "Denied", "Granted"],
        }
    )
    features = extract_event_features(df)
    assert features.loc[0, "user_event_count"] == 2
    assert features.loc[2, "door_event_count"] == 1
