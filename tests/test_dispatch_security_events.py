from __future__ import annotations

from yosai_intel_dashboard.src.services.analytics.security_patterns import (
    SecurityEvent,
    _dispatch_security_events,
    setup_isolated_security_testing,
)
from yosai_intel_dashboard.src.services.analytics.security_patterns.pattern_detection import (
    Threat,
)


def test_dispatch_security_events_with_threat():
    class DummyFrame:
        def __len__(self) -> int:
            return 3

    with setup_isolated_security_testing() as env:
        prepared = DummyFrame()
        threat = Threat("dummy", {})
        _dispatch_security_events(prepared, [threat])
        assert env.events[SecurityEvent.THREAT_DETECTED] == [{"threats": [threat]}]
        assert env.events[SecurityEvent.ANALYSIS_COMPLETE] == [{"records": 3}]


def test_dispatch_security_events_without_threat():
    class DummyFrame:
        def __len__(self) -> int:
            return 2

    with setup_isolated_security_testing() as env:
        prepared = DummyFrame()
        _dispatch_security_events(prepared, [])
        assert env.events[SecurityEvent.THREAT_DETECTED] == []
        assert env.events[SecurityEvent.ANALYSIS_COMPLETE] == [{"records": 2}]
