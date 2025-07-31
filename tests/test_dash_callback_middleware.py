from __future__ import annotations

import dash
from dash import Output

from core.dash_callback_middleware import wrap_callback
from core.error_handling import error_handler
from validation.security_validator import SecurityValidator


def test_wrap_callback_validation(monkeypatch):
    outputs = (Output("o", "children"),)
    called = {}

    def cb(value):
        called["v"] = value
        return value

    wrapper = wrap_callback(cb, outputs, SecurityValidator())
    # valid input
    assert wrapper("ok") == "ok"
    assert called["v"] == "ok"

    called.clear()
    result = wrapper("<script>")
    assert result is dash.no_update
    assert called == {}


def test_wrap_callback_error_logged(monkeypatch):
    outputs = (Output("o", "children"),)

    def cb(value):
        raise RuntimeError("boom")

    recorded = {}

    def fake_handle_error(exc, *, severity, context):
        recorded["exc"] = exc
        recorded["ctx"] = context

    monkeypatch.setattr(error_handler, "handle_error", fake_handle_error)
    wrapper = wrap_callback(cb, outputs, SecurityValidator())
    out = wrapper("ok")
    assert out is dash.no_update
    assert isinstance(recorded.get("exc"), RuntimeError)
    assert "callback" in recorded.get("ctx", {})
