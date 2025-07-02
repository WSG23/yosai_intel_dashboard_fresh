import pandas as pd
from services import analytics_service
from services.pattern_analysis import calculate_pattern_stats, calculate_success_rate


def _make_df():
    return pd.DataFrame({
        "person_id": ["u1", "u2", "u1"],
        "door_id": ["d1", "d2", "d1"],
        "access_result": ["Granted", "Denied", "Granted"],
        "timestamp": ["2024-01-01", "2024-01-02", "2024-01-03"],
    })


def test_calculate_pattern_stats():
    df = _make_df()
    total, users, devices, span = calculate_pattern_stats(df)
    assert total == 3
    assert users == 2
    assert devices == 2
    assert span == 2


def test_calculate_success_rate():
    df = _make_df()
    rate = calculate_success_rate(df)
    assert 0 < rate <= 1
