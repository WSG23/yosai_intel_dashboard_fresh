from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

module_path = (
    Path(__file__).resolve().parents[2]
    / "yosai_intel_dashboard/src/infrastructure/security/audit_logger.py"
)
spec = importlib.util.spec_from_file_location("audit_logger", module_path)
audit_module = importlib.util.module_from_spec(spec)
assert spec and spec.loader  # type: ignore[truthy-function]
sys.modules["audit_logger"] = audit_module
spec.loader.exec_module(audit_module)
SecurityAuditLogger = audit_module.SecurityAuditLogger


def test_security_audit_logger_appends_and_alerts(tmp_path, monkeypatch):
    # capture SIEM events
    events = []

    def mock_send(event, system):
        events.append((event, system))

    monkeypatch.setattr(audit_module, "send_to_siem", mock_send)

    notifications = []

    class DummyAlertManager:
        def _notify(self, message):
            notifications.append(message)

    class DummyDetector:
        def score(self, user_id, source_ip):
            return 0.0, True  # always anomaly

    log_file = tmp_path / "audit.log"
    logger = SecurityAuditLogger(
        log_path=log_file,
        alert_manager=DummyAlertManager(),
        anomaly_detector=DummyDetector(),
    )

    logger.log_auth_event(
        user_id="u1", action="login", success=False, source_ip="1.1.1.1"
    )
    logger.log_permission_event(
        user_id="u1", permission="admin", granted=False, resource="/secure"
    )

    lines = log_file.read_text().splitlines()
    assert len(lines) == 2
    record = json.loads(lines[0])
    assert record["type"] == "auth"
    assert events[0][0]["type"] == "auth"
    assert notifications, "Expected alert notification for anomaly"


def test_security_audit_logger_handles_write_failure(tmp_path, monkeypatch):
    events = []

    def mock_send(event, system):
        events.append((event, system))

    monkeypatch.setattr(audit_module, "send_to_siem", mock_send)

    notifications = []

    class DummyAlertManager:
        def _notify(self, message):
            notifications.append(message)

    class DummyDetector:
        def score(self, user_id, source_ip):
            return 0.0, False

    log_file = tmp_path / "audit.log"
    logger = SecurityAuditLogger(
        log_path=log_file,
        alert_manager=DummyAlertManager(),
        anomaly_detector=DummyDetector(),
    )

    def fail_open(*args, **kwargs):
        raise OSError("read-only file system")

    monkeypatch.setattr(Path, "open", fail_open)

    logger.log_auth_event(user_id="u1", action="login", success=True)

    assert notifications, "Expected alert notification for write failure"
    assert not events, "SIEM should not receive event on write failure"
    assert not log_file.exists(), "Log file should not be created"
