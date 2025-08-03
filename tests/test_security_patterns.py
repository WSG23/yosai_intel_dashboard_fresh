from __future__ import annotations

import inspect

import pandas as pd

from analytics.security_patterns import SecurityPatternsAnalyzer, prepare_security_data
from analytics.security_patterns.pattern_detection import detect_critical_door_risks


def test_analyze_failed_access_returns_expected_keys(monkeypatch):
    class DummyConn:
        def execute_query(self, *a, **kw):
            return []

        def execute_command(self, *a, **kw):
            return 0

        def execute_batch(self, *a, **kw):
            return 0

        def health_check(self) -> bool:
            return True

    analyzer = SecurityPatternsAnalyzer()
    df = pd.DataFrame(
        {
            "event_id": [1, 2, 3, 4, 5],
            "timestamp": pd.date_range("2024-01-01 08:00:00", periods=5, freq="H"),
            "person_id": ["u1", "u1", "u2", "u1", "u3"],
            "door_id": ["d1", "d2", "d2", "d1", "d1"],
            "access_result": ["Denied"] * 5,
        }
    )
    prepared = analyzer._prepare_data(df)
    result = analyzer._analyze_failed_access(prepared)
    expected_keys = {
        "total",
        "failure_rate",
        "high_risk_users",
        "peak_failure_times",
        "top_failure_doors",
        "patterns",
        "risk_level",
    }
    assert set(result.keys()) == expected_keys


def test_detect_critical_door_risks():
    df = pd.DataFrame(
        {
            "event_id": [1, 2],
            "timestamp": [
                "2024-01-01 23:30:00",
                "2024-01-01 23:45:00",
            ],
            "person_id": ["u1", "u1"],
            "door_id": ["d_critical", "d_critical"],
            "access_result": ["Denied", "Denied"],
            "door_type": ["critical", "critical"],
            "required_clearance": [4, 4],
            "clearance_level": [1, 1],
        }
    )
    prepared = prepare_security_data(df)
    threats = list(detect_critical_door_risks(prepared))
    assert any(t.threat_type == "critical_door_anomaly" for t in threats)


def test_detect_odd_time_zero_variance(monkeypatch):
    class DummyBaseline:
        def get_baseline(self, *a, **kw):
            return {}

        def update_baseline(self, *a, **kw):
            pass

    monkeypatch.setattr(
        "analytics.security_patterns.odd_time_detection.BaselineMetricsDB",
        lambda: DummyBaseline(),
    )

    df = pd.DataFrame({"person_id": ["u1", "u1"], "hour": [10, 10]})
    from analytics.security_patterns.odd_time_detection import detect_odd_time

    threats = list(detect_odd_time(df))
    assert threats == []


def test_detect_odd_time_zero_baseline_std(monkeypatch):
    class DummyBaseline:
        def get_baseline(self, *a, **kw):
            return {"mean_hour": 10, "std_hour": 0}

        def update_baseline(self, *a, **kw):
            pass

    monkeypatch.setattr(
        "analytics.security_patterns.odd_time_detection.BaselineMetricsDB",
        lambda: DummyBaseline(),
    )

    df = pd.DataFrame({"person_id": ["u1", "u1"], "hour": [10, 12]})
    from analytics.security_patterns.odd_time_detection import detect_odd_time

    threats = list(detect_odd_time(df))
    assert len(threats) == 1


def test_detection_functions_return_generators():
    """Ensure detection helpers provide generators for lazy iteration."""
    df_cd = pd.DataFrame(
        columns=["door_type", "access_result", "clearance_level", "required_clearance"]
    )
    prepared_cd = prepare_security_data(df_cd)
    assert inspect.isgenerator(detect_critical_door_risks(prepared_cd))

    from analytics.security_patterns.odd_time_detection import detect_odd_time

    df_ot = pd.DataFrame(columns=["person_id", "hour"])
    assert inspect.isgenerator(detect_odd_time(df_ot))
