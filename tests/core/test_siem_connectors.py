from __future__ import annotations

import logging

from yosai_intel_dashboard.src.core.integrations.siem_connectors import send_to_siem


def test_send_to_siem_logs_event(caplog):
    event = {"type": "auth", "user": "alice"}
    with caplog.at_level(logging.INFO):
        send_to_siem(event, "splunk")
    assert any(
        rec.levelno == logging.INFO
        and rec.name == "yosai_intel_dashboard.src.core.integrations.siem_connectors"
        and rec.getMessage() == f"Sending event to splunk: {event}"
        for rec in caplog.records
    )
