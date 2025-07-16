import pandas as pd

from analytics.security_patterns.data_prep import prepare_security_data
from analytics.security_patterns.analyzer import SecurityPatternsAnalyzer
from analytics.security_patterns.critical_door_detection import detect_critical_door_anomalies
from analytics.security_patterns.tailgate_detection import detect_tailgate
from analytics.security_patterns.badge_clone_detection import detect_badge_clone
from analytics.security_patterns.odd_door_detection import detect_odd_door_usage
from analytics.security_patterns.odd_time_detection import detect_odd_time
from analytics.security_patterns.odd_path_detection import detect_odd_path
from analytics.security_patterns.odd_area_detection import detect_odd_area
from analytics.security_patterns.odd_area_time_detection import detect_odd_area_time
from analytics.security_patterns.multiple_attempts_detection import detect_multiple_attempts
from analytics.security_patterns.forced_entry_detection import detect_forced_entry
from analytics.security_patterns.access_no_exit_detection import detect_access_no_exit
from analytics.security_patterns.pattern_drift_detection import detect_pattern_drift
from analytics.security_patterns.clearance_violation_detection import detect_clearance_violations
from analytics.security_patterns.unaccompanied_visitor_detection import detect_unaccompanied_visitors
from analytics.security_patterns.composite_score import detect_composite_score
from analytics.security_patterns.types import ThreatIndicator


SAMPLE_ROWS = [
    {
        "timestamp": "2024-01-01 01:00:00",
        "person_id": "u1",
        "door_id": "A-1",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 1,
    },
    {
        "timestamp": "2024-01-01 01:00:03",
        "person_id": "u2",
        "door_id": "A-1",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Visitor",
        "user_clearance": 1,
        "required_clearance": 1,
    },
    {
        "timestamp": "2024-01-01 01:00:30",
        "person_id": "u1",
        "door_id": "B-1",
        "access_result": "Denied",
        "door_held_open_time": 12,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 3,
    },
    {
        "timestamp": "2024-01-01 02:00:00",
        "person_id": "u1",
        "door_id": "C-1",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 2,
    },
    {
        "timestamp": "2024-01-01 02:01:00",
        "person_id": "u1",
        "door_id": "C-2",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 2,
    },
    {
        "timestamp": "2024-01-02 10:00:00",
        "person_id": "u2",
        "door_id": "A-2",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Visitor",
        "user_clearance": 1,
        "required_clearance": 1,
    },
]

SAFE_ROWS = [
    {
        "timestamp": "2024-01-01 10:00:00",
        "person_id": "u1",
        "door_id": "A-1",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 1,
    },
    {
        "timestamp": "2024-01-01 10:05:00",
        "person_id": "u1",
        "door_id": "A-1",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 1,
    },
    {
        "timestamp": "2024-01-01 10:10:00",
        "person_id": "u1",
        "door_id": "A-1",
        "access_result": "Granted",
        "door_held_open_time": 0,
        "badge_status": "Employee",
        "user_clearance": 2,
        "required_clearance": 1,
    },
]


class DummyBaselineDB:
    def __init__(self):
        self.store = {}

    def update_baseline(self, entity_type: str, entity_id: str, metrics: dict):
        self.store.setdefault((entity_type, entity_id), {}).update(metrics)

    def get_baseline(self, entity_type: str, entity_id: str) -> dict:
        return self.store.get((entity_type, entity_id), {})


class PreloadedBaselineDB(DummyBaselineDB):
    """Baseline DB seeded with values to trigger anomalies."""

    def __init__(self):
        super().__init__()
        self.store = {
            ("user", "u1"): {"door_A-1_rate": 0.1, "mean_hour": 8, "std_hour": 1},
            ("global", "overall"): {"after_hours_rate": 0.0, "failure_rate": 0.0},
        }


class SafeBaselineDB(DummyBaselineDB):
    """Baseline values matching SAFE_ROWS so no anomalies are produced."""

    def __init__(self):
        super().__init__()
        self.store = {
            ("user", "u1"): {"door_A-1_rate": 1.0, "mean_hour": 10, "std_hour": 1},
            ("global", "overall"): {"after_hours_rate": 0.0, "failure_rate": 0.0},
        }


def _prepare_df(rows):
    df = pd.DataFrame(rows)
    return prepare_security_data(df)


def test_detectors_produce_indicators(monkeypatch):
    df = _prepare_df(SAMPLE_ROWS)
    monkeypatch.setattr(
        "analytics.security_patterns.odd_door_detection.BaselineMetricsDB",
        PreloadedBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.odd_time_detection.BaselineMetricsDB",
        PreloadedBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.pattern_drift_detection.BaselineMetricsDB",
        PreloadedBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.analyzer.BaselineMetricsDB",
        PreloadedBaselineDB,
    )

    funcs = [
        (detect_critical_door_anomalies, ("high", "critical_door_anomaly")),
        (detect_tailgate, ("medium", "probable_tailgate")),
        (detect_badge_clone, ("high", "badge_clone_suspected")),
        (detect_odd_door_usage, ("medium", "odd_door_anomaly")),
        (detect_odd_time, ("medium", "odd_time_anomaly")),
        (detect_odd_path, ("low", "odd_path_anomaly")),
        (detect_odd_area, ("low", "odd_area_anomaly")),
        (detect_odd_area_time, ("medium", "odd_area_time_anomaly")),
        (detect_multiple_attempts, ("high", "multiple_attempts_anomaly")),
        (detect_forced_entry, ("high", "forced_entry_or_door_held_open")),
        (detect_access_no_exit, ("medium", "access_granted_no_exit_anomaly")),
        (detect_pattern_drift, ("medium", "access_pattern_drift_anomaly")),
        (detect_clearance_violations, ("high", "access_outside_clearance_anomaly")),
        (detect_unaccompanied_visitors, ("medium", "unaccompanied_visitor_anomaly")),
        (detect_composite_score, ("low", "composite_anomaly_score")),
    ]

    for func, (severity, threat_type) in funcs:
        threats = func(df)
        assert threats, f"{func.__name__} produced no indicators"
        assert isinstance(threats[0], ThreatIndicator)
        assert threats[0].severity == severity
        assert threats[0].threat_type == threat_type


def test_detectors_no_anomalies(monkeypatch):
    df = _prepare_df(SAFE_ROWS)
    monkeypatch.setattr(
        "analytics.security_patterns.odd_door_detection.BaselineMetricsDB",
        SafeBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.odd_time_detection.BaselineMetricsDB",
        SafeBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.pattern_drift_detection.BaselineMetricsDB",
        SafeBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.analyzer.BaselineMetricsDB",
        SafeBaselineDB,
    )

    funcs = [
        detect_critical_door_anomalies,
        detect_tailgate,
        detect_badge_clone,
        detect_odd_door_usage,
        detect_odd_time,
        detect_odd_path,
        detect_odd_area,
        detect_odd_area_time,
        detect_multiple_attempts,
        detect_forced_entry,
        detect_access_no_exit,
        detect_pattern_drift,
        detect_clearance_violations,
        detect_unaccompanied_visitors,
        detect_composite_score,
    ]

    for func in funcs:
        threats = func(df)
        assert threats == []


def test_analyzer_integration(monkeypatch):
    df = _prepare_df(SAMPLE_ROWS)
    monkeypatch.setattr(
        "analytics.security_patterns.analyzer.BaselineMetricsDB",
        PreloadedBaselineDB,
    )
    analyzer = SecurityPatternsAnalyzer()
    result = analyzer.analyze_security_patterns(df)
    assert isinstance(result.threat_indicators, list)
