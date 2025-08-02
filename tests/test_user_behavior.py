import pandas as pd
import pytest

from services.analytics.user_behavior import UserBehaviorAnalyzer


def create_analyzer(df):
    analyzer = UserBehaviorAnalyzer()
    prepared = analyzer._prepare_data(df)
    return analyzer, prepared


def test_generate_behavior_summary_basic():
    df = pd.DataFrame(
        [
            {
                "person_id": "U1",
                "door_id": "D1",
                "timestamp": "2024-01-01 09:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": "U1",
                "door_id": "D2",
                "timestamp": "2024-01-01 10:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": "U2",
                "door_id": "D1",
                "timestamp": "2024-01-02 23:00:00",
                "access_result": "Denied",
            },
            {
                "person_id": "U2",
                "door_id": "D3",
                "timestamp": "2024-01-02 23:30:00",
                "access_result": "Granted",
            },
        ]
    )
    analyzer, prepared = create_analyzer(df)
    summary = analyzer._generate_behavior_summary(prepared)

    assert summary["total_unique_users"] == 2
    assert summary["avg_events_per_user"] == 2
    assert summary["overall_success_rate"] == 75.0
    assert summary["activity_distribution"]["after_hours_users"] == 1


def test_generate_behavior_summary_missing_person_ids():
    df = pd.DataFrame(
        [
            {
                "person_id": None,
                "door_id": "D1",
                "timestamp": "2024-01-01 09:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": None,
                "door_id": "D1",
                "timestamp": "2024-01-01 10:00:00",
                "access_result": "Denied",
            },
        ]
    )
    analyzer, prepared = create_analyzer(df)
    summary = analyzer._generate_behavior_summary(prepared)

    assert summary["total_unique_users"] == 0
    assert summary["avg_events_per_user"] == 0


def test_calculate_user_risk_score():
    df = pd.DataFrame(
        [
            {
                "person_id": "U1",
                "door_id": "D1",
                "timestamp": "2024-01-01 09:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": "U1",
                "door_id": "D1",
                "timestamp": "2024-01-02 23:00:00",
                "access_result": "Denied",
            },
            {
                "person_id": "U2",
                "door_id": "D1",
                "timestamp": "2024-01-03 09:00:00",
                "access_result": "Granted",
            },
            {
                "person_id": "U2",
                "door_id": "D1",
                "timestamp": "2024-01-04 09:00:00",
                "access_result": "Granted",
            },
        ]
    )
    analyzer, prepared = create_analyzer(df)
    user_data = prepared[prepared["person_id"] == "U1"]
    score = analyzer._calculate_user_risk_score(user_data, prepared)
    assert score == pytest.approx(30.0)


def test_calculate_regularity_score():
    analyzer = UserBehaviorAnalyzer()
    daily_counts = pd.Series([5, 5, 5])
    score = analyzer._calculate_regularity_score(daily_counts)
    assert score == pytest.approx(1.0)


def test_calculate_temporal_diversity():
    df = pd.DataFrame(
        {
            "hour": [1, 1, 2, 2, 3, 3, 4, 4],
            "day_of_week": ["Mon", "Mon", "Tue", "Tue", "Wed", "Wed", "Thu", "Thu"],
        }
    )
    analyzer = UserBehaviorAnalyzer()
    result = analyzer._calculate_temporal_diversity(df)

    import numpy as np

    hour_entropy = -np.sum([0.25 * np.log2(0.25)] * 4)
    expected_hour = hour_entropy / np.log2(24)

    day_entropy = -np.sum([0.25 * np.log2(0.25)] * 4)
    expected_day = day_entropy / np.log2(7)

    assert result["hour_diversity"] == pytest.approx(expected_hour)
    assert result["day_diversity"] == pytest.approx(expected_day)
    assert result["overall_temporal_diversity"] == pytest.approx(
        (expected_hour + expected_day) / 2
    )
