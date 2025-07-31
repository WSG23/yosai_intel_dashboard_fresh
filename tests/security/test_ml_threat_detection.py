import pytest

import security.ml_threat_detection as mlt
from security.events import SecurityEvent


@pytest.mark.asyncio
async def test_model_invocation_and_threat_creation(monkeypatch):
    called = {}

    async def dummy_model(features):
        called["features"] = features
        return [
            {
                "type": "intrusion",
                "level": "high",
                "score": 0.9,
                "metadata": {"ip": "1.2.3.4"},
            }
        ]

    engine = mlt.MLSecurityEngine(dummy_model)
    events = [{"ip": "1.2.3.4"}]

    emitted = []
    monkeypatch.setattr(
        mlt, "emit_security_event", lambda e, data=None: emitted.append((e, data))
    )
    monkeypatch.setattr(
        mlt.security_auditor, "log_security_event", lambda *a, **k: None
    )

    threats = await engine.analyze_security_events(events)

    assert called["features"] == events
    assert len(threats) == 1
    threat = threats[0]
    assert threat.threat_type == "intrusion"
    assert threat.level == mlt.ThreatLevel.HIGH
    assert threat.metadata["ip"] == "1.2.3.4"
    assert emitted and emitted[0][0] == SecurityEvent.THREAT_DETECTED
