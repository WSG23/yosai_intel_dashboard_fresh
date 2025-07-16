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


class DummyBaselineDB:
    def __init__(self):
        self.store = {}

    def update_baseline(self, entity_type: str, entity_id: str, metrics: dict):
        self.store.setdefault((entity_type, entity_id), {}).update(metrics)

    def get_baseline(self, entity_type: str, entity_id: str) -> dict:
        return self.store.get((entity_type, entity_id), {})


def _prepare_df():
    df = pd.DataFrame(SAMPLE_ROWS)
    return prepare_security_data(df)


def test_all_detectors_return_list(monkeypatch):
    df = _prepare_df()
    monkeypatch.setattr(
        "analytics.security_patterns.odd_door_detection.BaselineMetricsDB",
        DummyBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.odd_time_detection.BaselineMetricsDB",
        DummyBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.pattern_drift_detection.BaselineMetricsDB",
        DummyBaselineDB,
    )
    monkeypatch.setattr(
        "analytics.security_patterns.analyzer.BaselineMetricsDB",
        DummyBaselineDB,
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
        assert isinstance(threats, list)


def test_analyzer_integration(monkeypatch):
    df = _prepare_df()
    monkeypatch.setattr(
        "analytics.security_patterns.analyzer.BaselineMetricsDB",
        DummyBaselineDB,
    )
    analyzer = SecurityPatternsAnalyzer()
    result = analyzer.analyze_security_patterns(df)
    assert isinstance(result.threat_indicators, list)
