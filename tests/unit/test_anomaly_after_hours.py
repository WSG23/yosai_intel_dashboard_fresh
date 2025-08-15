"""Tests for configurable after-hours anomaly detection."""

from __future__ import annotations

from yosai_intel_dashboard.src.core.domain.entities.base import AnomalyDetectionModel
from yosai_intel_dashboard.src.infrastructure.config import constants


def test_detects_after_hours_by_default() -> None:
    model = AnomalyDetectionModel(None)
    events = [{"timestamp": "2024-04-22 23:00", "access_result": "Granted"}]

    anomalies = model.detect_anomalies(events)

    assert any(a["type"] == "after_hours_access" for a in anomalies)


def test_custom_after_hours(monkeypatch) -> None:
    model = AnomalyDetectionModel(None)
    events = [{"timestamp": "2024-04-22 09:00", "access_result": "Granted"}]

    monkeypatch.setattr(constants, "AFTER_HOURS", ["09:"])
    anomalies = model.detect_anomalies(events)

    assert any(a["type"] == "after_hours_access" for a in anomalies)

