import json
import logging

import pytest

from python.yosai_framework import service as svc_mod
from python.yosai_framework.config import ServiceConfig


def _dummy_config(*_):
    return ServiceConfig(service_name="test", log_level="INFO", metrics_addr="", tracing_endpoint="")


def test_structlog_json(monkeypatch, caplog):
    monkeypatch.setattr(svc_mod, "load_config", _dummy_config)
    svc = svc_mod.BaseService("test", "cfg")
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
    svc = svc_mod.BaseService("test", "cfg")
    svc.start()
    names = svc_mod.REGISTRY._names_to_collectors.keys()
    assert "yosai_request_total" in names
    assert "yosai_request_duration_seconds" in names
    assert "yosai_error_total" in names
    svc.stop()
