import numpy as np
import pandas as pd

from services.analytics.unique_patterns_analyzer import UniquePatternAnalyzer


def sample_df():
    return pd.DataFrame(
        [
            {
                "person_id": "U1",
                "door_id": "D1",
                "timestamp": "2024-01-01 08:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": "U1",
                "door_id": "D2",
                "timestamp": "2024-01-01 09:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": "U2",
                "door_id": "D1",
                "timestamp": "2024-01-01 10:00:00",
                "access_result": "Denied",
            },
            {
                "person_id": "U2",
                "door_id": "D1",
                "timestamp": "2024-01-01 11:00:00",
                "access_result": "Granted",
            },
        ]
    )


def test_prepare_data_adds_columns():
    analyzer = UniquePatternAnalyzer()
    prepared = analyzer._prepare_data(sample_df())

    assert {"hour", "day_of_week", "date", "access_granted", "event_id"}.issubset(
        prepared.columns
    )
    assert prepared.loc[0, "hour"] == 8
    assert prepared.loc[0, "access_granted"] == True


def test_analyze_unique_users_basic():
    analyzer = UniquePatternAnalyzer()
    prepared = analyzer._prepare_data(sample_df())
    result = analyzer._analyze_unique_users(prepared)

    assert result["total_unique_users"] == 2
    assert result["active_users"] == 0
    assert set(result["top_users"].keys()) == {"U1", "U2"}


def test_analyze_unique_devices_basic():
    analyzer = UniquePatternAnalyzer()
    prepared = analyzer._prepare_data(sample_df())
    result = analyzer._analyze_unique_devices(prepared)

    assert result["total_unique_devices"] == 2
    assert result["active_devices"] == 1
    assert set(result["top_devices"].keys()) == {"D1", "D2"}


def test_prepare_data_no_timestamp():
    analyzer = UniquePatternAnalyzer()
    df = sample_df().drop(columns=["timestamp"])
    prepared = analyzer._prepare_data(df)

    assert "hour" not in prepared.columns
    temporal = analyzer._analyze_temporal_uniqueness(prepared)
    assert temporal["status"] == "missing_temporal_data"


def test_analyze_patterns_empty_df():
    analyzer = UniquePatternAnalyzer()
    result = analyzer.analyze_patterns(pd.DataFrame(), {})
    assert result["status"] == "no_data"


def test_prepare_data_memory_profile():
    rows = 10000
    df = pd.DataFrame(
        {
            "person_id": [f"U{i%10}" for i in range(rows)],
            "door_id": [f"D{i%5}" for i in range(rows)],
            "timestamp": pd.date_range("2024-01-01", periods=rows, freq="min"),
            "access_result": ["Granted"] * rows,
        }
    )

    analyzer = UniquePatternAnalyzer()

    # Simulate deep-copy processing for baseline memory usage
    deep_copy = df.copy()
    deep_copy["timestamp"] = pd.to_datetime(deep_copy["timestamp"])
    deep_copy["hour"] = deep_copy["timestamp"].dt.hour
    deep_copy["day_of_week"] = deep_copy["timestamp"].dt.day_name()
    deep_copy["date"] = deep_copy["timestamp"].dt.date
    deep_copy["access_granted"] = (
        deep_copy["access_result"].str.lower().isin(["granted", "success", "true", "1"])
    )
    deep_copy["event_id"] = range(len(deep_copy))
    deep_memory = deep_copy.memory_usage(deep=True).sum()

    prepared = analyzer._prepare_data(df)
    prepared_memory = prepared.memory_usage(deep=True).sum()

    # The shallow-copy approach should not use more memory than the deep-copy baseline
    assert prepared_memory <= deep_memory
