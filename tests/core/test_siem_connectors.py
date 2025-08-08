import logging

from yosai_intel_dashboard.src.core.integrations.siem_connectors import send_to_siem


def test_send_to_siem_logs_event(caplog):
    event = {"foo": "bar"}
    with caplog.at_level(
        logging.INFO,
        logger="yosai_intel_dashboard.src.core.integrations.siem_connectors",
    ):
        send_to_siem(event, "elk")
    messages = [
        r.getMessage()
        for r in caplog.records
        if r.name == "yosai_intel_dashboard.src.core.integrations.siem_connectors"
    ]
    assert any("Sending event to elk" in m for m in messages)
