import logging
import pytest
import requests

from cli.feature_flags import create_flag, list_flags
from yosai_intel_dashboard.src.exceptions import ExternalServiceError
from yosai_intel_dashboard.src.logging_config import configure_logging


configure_logging()


def test_list_flags_timeout(monkeypatch, caplog):
    def fake_get(*args, **kwargs):
        raise requests.Timeout("boom")

    monkeypatch.setattr(requests, "get", fake_get)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ExternalServiceError):
            list_flags("http://example.com", token="secret", roles=None)
    assert "secret" not in caplog.text


def test_create_flag_request_error(monkeypatch, caplog):
    def fake_post(*args, **kwargs):
        raise requests.ConnectionError("down")

    monkeypatch.setattr(requests, "post", fake_post)
    with caplog.at_level(logging.ERROR):
        with pytest.raises(ExternalServiceError):
            create_flag(
                "http://example.com", "new_flag", True, token=None, roles=None
            )

