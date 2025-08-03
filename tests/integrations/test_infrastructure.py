from __future__ import annotations

from datetime import datetime

from integrations.infrastructure import (
    ISPStatusClient,
    MunicipalAlertClient,
    PowerGridClient,
)
from yosai_intel_dashboard.src.database.infrastructure_events import (
    InfrastructureEvent,
    clear_events,
    get_active_events,
    record_event,
)
from yosai_intel_dashboard.src.infrastructure.monitoring.alerts import (
    AlertManager,
    AlertThresholds,
)


def test_clients_ingest_events(monkeypatch):
    now = datetime.utcnow()
    clients = [
        (PowerGridClient(), "power-grid"),
        (ISPStatusClient(), "isp"),
        (MunicipalAlertClient(), "municipal"),
    ]
    clear_events()
    for client, source in clients:
        event = InfrastructureEvent(
            source=source,
            description="outage",
            start_time=now,
        )
        monkeypatch.setattr(client, "fetch_events", lambda e=event: [e])
        client.ingest()

    events = get_active_events()
    assert {e.source for e in events} == {"power-grid", "isp", "municipal"}


def test_alert_enrichment(monkeypatch):
    clear_events()
    now = datetime.utcnow()
    record_event(
        InfrastructureEvent(
            source="isp",
            description="degradation",
            start_time=now,
        )
    )

    class DummyNotifier:
        def __init__(self):
            self.messages: list[str] = []

        def send(self, message: str) -> None:  # pragma: no cover - simple
            self.messages.append(message)

    dummy = DummyNotifier()
    monkeypatch.setattr(
        "yosai_intel_dashboard.src.infrastructure.monitoring.alerts.NotificationService",
        lambda: dummy,
    )

    manager = AlertManager(thresholds=AlertThresholds())
    manager._notify("security incident")
    assert dummy.messages
    msg = dummy.messages[0]
    assert "security incident" in msg
    assert "degradation" in msg
