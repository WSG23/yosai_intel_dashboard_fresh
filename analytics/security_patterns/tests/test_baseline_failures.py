import pandas as pd
from analytics.security_patterns.tests.test_additional_detectors import _prepare_df
from analytics.security_patterns.odd_door_detection import detect_odd_door_usage
from analytics.security_patterns.odd_time_detection import detect_odd_time
from analytics.security_patterns.pattern_drift_detection import detect_pattern_drift


class FailingBaselineDB:
    def __init__(self, *args, **kwargs):
        pass

    def update_baseline(self, *args, **kwargs):
        raise RuntimeError("db error")

    def get_baseline(self, *args, **kwargs):
        return {}


def test_detectors_handle_baseline_update_error(monkeypatch):
    df = _prepare_df()
    monkeypatch.setattr(
        "analytics.security_patterns.odd_door_detection.BaselineMetricsDB",
        FailingBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.odd_time_detection.BaselineMetricsDB",
        FailingBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.pattern_drift_detection.BaselineMetricsDB",
        FailingBaselineDB,
    )

    assert isinstance(detect_odd_door_usage(df), list)
    assert isinstance(detect_odd_time(df), list)
    assert isinstance(detect_pattern_drift(df), list)
