from __future__ import annotations

import importlib.util
import json
import logging
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


def test_security_audit_logger_appends_and_alerts(tmp_path, caplog):
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

    with caplog.at_level(
        logging.INFO,
        logger="yosai_intel_dashboard.src.core.integrations.siem_connectors",
    ):
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
    messages = [
        r.getMessage()
        for r in caplog.records
        if r.name == "yosai_intel_dashboard.src.core.integrations.siem_connectors"
    ]
    assert any("Sending event to elk" in m for m in messages)
    assert notifications, "Expected alert notification for anomaly"
