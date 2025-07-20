import pandas as pd

from services.analytics_service import AnalyticsService


def _make_df():
    return pd.DataFrame(
        {
            "person_id": ["u1", "u2", "u1"],
            "door_id": ["d1", "d2", "d1"],
            "access_result": ["Granted", "Denied", "Granted"],
            "timestamp": [
                "2024-01-01 10:00:00",
                "2024-01-02 11:00:00",
                "2024-01-02 12:00:00",
            ],
        }
    )


def test_calculate_stats():
    service = AnalyticsService()
    df = _make_df()
    total, users, devices, span = service._calculate_stats(df)
    assert total == len(df)
    assert users == 2
    assert devices == 2
    assert span == 1


def test_analyze_users():
    service = AnalyticsService()
    df = _make_df()
    power, regular, occasional = service._analyze_users(df, 2)
    assert power == ["u1"]
    assert regular == []
    assert occasional == ["u2"]


def test_analyze_devices():
    service = AnalyticsService()
    df = _make_df()
    high, moderate, low = service._analyze_devices(df, 2)
    assert high == ["d1"]
    assert moderate == []
    assert low == ["d2"]


def test_log_analysis_summary(caplog):
    service = AnalyticsService()
    with caplog.at_level("INFO"):
        service._log_analysis_summary(3, 3)
    messages = [r.getMessage() for r in caplog.records]
    assert any("UNIQUE PATTERNS ANALYSIS COMPLETE" in m for m in messages)
    assert any("Correctly showing 3" in m for m in messages)
