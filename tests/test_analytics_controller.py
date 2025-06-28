import pandas as pd
import pytest

from analytics.analytics_controller import AnalyticsController, AnalyticsConfig


class DummySecurityAnalyzer:
    def __init__(self):
        self.calls = 0

    def analyze_patterns(self, df):
        self.calls += 1
        return {"security": True}


class DummyTrendsAnalyzer:
    def __init__(self):
        self.calls = 0

    def analyze_trends(self, df):
        self.calls += 1
        return {"trends": True}


def create_controller(cache_results=False):
    config = AnalyticsConfig(
        enable_security_patterns=True,
        enable_access_trends=True,
        enable_user_behavior=False,
        enable_anomaly_detection=False,
        enable_interactive_charts=False,
        parallel_processing=False,
        cache_results=cache_results,
    )
    controller = AnalyticsController(config)
    controller.security_analyzer = DummySecurityAnalyzer()
    controller.trends_analyzer = DummyTrendsAnalyzer()
    return controller


def sample_df():
    return pd.DataFrame(
        {
            "event_id": [1, 2],
            "timestamp": ["2024-01-01 10:00:00", "2024-01-01 11:00:00"],
            "person_id": ["p1", "p2"],
            "door_id": ["d1", "d2"],
            "access_result": ["Granted", "Denied"],
        }
    )


def test_prepare_data_missing_and_duplicates():
    controller = create_controller()
    df = sample_df()
    # add duplicate and check removal
    df = pd.concat([df, df.iloc[[0]]], ignore_index=True)
    prepared = controller._prepare_data(df)
    assert len(prepared) == 2

    # missing column should raise
    df_missing = df.drop(columns=["door_id"])
    with pytest.raises(ValueError):
        controller._prepare_data(df_missing)

    # invalid timestamp should raise
    df_bad = sample_df()
    df_bad.loc[0, "timestamp"] = "badtime"
    with pytest.raises(Exception):
        controller._prepare_data(df_bad)


def test_generate_data_summary():
    controller = create_controller()
    empty_summary = controller._generate_data_summary(pd.DataFrame())
    assert empty_summary["total_events"] == 0
    assert empty_summary["data_quality"] == "empty"

    df = controller._prepare_data(sample_df())
    summary = controller._generate_data_summary(df)
    assert summary["total_events"] == 2
    assert summary["unique_users"] == 2
    assert summary["unique_doors"] == 2
    assert summary["access_success_rate"] == 50.0
    assert summary["data_quality"] == "excellent"


def test_analyze_all_triggers_callbacks_and_cache():
    controller = create_controller(cache_results=True)
    events = []
    controller.register_callback("on_analysis_start", lambda aid, df: events.append("start"))
    controller.register_callback("on_analysis_complete", lambda aid, res: events.append("complete"))

    df = sample_df()
    result1 = controller.analyze_all(df)
    assert events == ["start", "complete"]
    assert controller.security_analyzer.calls == 1

    result2 = controller.analyze_all(df)
    assert events == ["start", "complete", "start"]
    assert controller.security_analyzer.calls == 1
    assert result2 is result1
