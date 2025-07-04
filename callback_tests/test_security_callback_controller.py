import pandas as pd
from analytics.security_patterns import (
    SecurityPatternsAnalyzer,
    SecurityCallbackController,
    SecurityEvent,
    setup_isolated_security_testing,
)


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
    controller, _ = setup_isolated_security_testing()
    results = []

    def cb(data):
        results.append(data)

    controller.register_callback(SecurityEvent.THREAT_DETECTED, cb)
    controller.fire_event(SecurityEvent.THREAT_DETECTED, {"msg": "alert"})

    assert results == [{"msg": "alert"}]
    assert controller.history == [
        (SecurityEvent.THREAT_DETECTED, {"msg": "alert"})
    ]


def test_analyzer_triggers_callbacks():
    controller, _ = setup_isolated_security_testing()

    analyzer = SecurityPatternsAnalyzer(callback_controller=controller)
    df = create_df_with_critical_threat()
    analyzer.analyze_security_patterns(df)

    events = [e[0] for e in controller.history]
    assert SecurityEvent.THREAT_DETECTED in events
    assert SecurityEvent.ANALYSIS_COMPLETE in events
