import pandas as pd
import pytest

from services.analytics.security_patterns import (
    SecurityEvent,
    SecurityPatternsAnalyzer,
    setup_isolated_security_testing,
)
from security.events import security_unified_callbacks


def create_df_with_critical_threat():
    data = []
    ts = pd.Timestamp("2024-01-01 00:00:00")

    # Rapid denied attempts for the same user (triggers critical threat)
    for i in range(4):
        data.append(
            {
                "event_id": i,
                "timestamp": ts + pd.Timedelta(seconds=i * 10),
                "person_id": "baduser",
                "door_id": "d1",
                "access_result": "Denied",
            }
        )

    # Additional normal traffic
    for i in range(20):
        data.append(
            {
                "event_id": 100 + i,
                "timestamp": ts + pd.Timedelta(hours=1, minutes=i),
                "person_id": f"u{i%3}",
                "door_id": "d1",
                "access_result": "Granted",
            }
        )

    return pd.DataFrame(data)


def test_callback_registration_and_fire():
    controller = security_unified_callbacks
    controller.clear_all_callbacks()

    results = []

    def cb(data):
        results.append(data)

    controller.register_event(SecurityEvent.THREAT_DETECTED, cb)
    controller.trigger_event(SecurityEvent.THREAT_DETECTED, {"msg": "alert"})

    assert results == [{"msg": "alert"}]
    assert controller.history == [(SecurityEvent.THREAT_DETECTED, {"msg": "alert"})]


def test_analyzer_triggers_callbacks():
    controller = security_unified_callbacks
    controller.clear_all_callbacks()
    events = []

    controller.register_event(
        SecurityEvent.THREAT_DETECTED,
        lambda d: events.append(("threat", d)),
    )
    controller.register_event(
        SecurityEvent.ANALYSIS_COMPLETE,
        lambda d: events.append(("complete", d)),
    )

    analyzer = SecurityPatternsAnalyzer()
    df = create_df_with_critical_threat()
    analyzer.analyze_security_patterns(df)

    events = [e[0] for e in controller.history]
    assert SecurityEvent.THREAT_DETECTED in events
    assert SecurityEvent.ANALYSIS_COMPLETE in events


def test_setup_isolated_security_testing_not_implemented():
    """Ensure the setup helper clearly indicates unfinished logic."""
    with pytest.raises(NotImplementedError):
        setup_isolated_security_testing()
