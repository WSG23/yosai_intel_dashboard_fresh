import pandas as pd
from analytics.unique_patterns_analyzer import UniquePatternAnalyzer


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
    assert prepared.loc[0, "access_granted"] is True


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
