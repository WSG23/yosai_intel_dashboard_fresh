import json
import logging

import pytest

from yosai_framework import ServiceBuilder
from yosai_framework import service as svc_mod
from yosai_framework.config import ServiceConfig


def _dummy_config(*_):
    return ServiceConfig(
        service_name="test", log_level="INFO", metrics_addr="", tracing_endpoint=""
    )


def test_structlog_json(monkeypatch, caplog):
    monkeypatch.setattr(svc_mod, "load_config", _dummy_config)
    svc = (
        ServiceBuilder("test")
        .with_config("cfg")
        .with_logging()
        .with_metrics("")
        .with_health()
        .build()
    )
    with caplog.at_level(logging.INFO):
        svc.start()
        svc.log.info("hello")
    records = [r for r in caplog.records if r.name == "test"]
    assert records
    data = json.loads(records[-1].getMessage())
    assert data["event"] == "hello"
    assert data["level"] == "info"


def test_metrics_registered(monkeypatch):
    monkeypatch.setattr(svc_mod, "load_config", _dummy_config)
    svc = (
        ServiceBuilder("test")
        .with_config("cfg")
        .with_logging()
        .with_metrics("")
        .with_health()
        .build()
    )
    svc.start()
    names = svc_mod.REGISTRY._names_to_collectors.keys()
    assert "yosai_request_total" in names
    assert "yosai_request_duration_seconds" in names
    assert "yosai_error_total" in names
    assert "yosai_request_memory_mb" in names
    svc.stop()
