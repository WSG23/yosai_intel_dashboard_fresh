import asyncio
import pytest

from dash import Dash
from dash.dependencies import Input, Output

from core.master_callback_system import MasterCallbackSystem
from core.callback_events import CallbackEvent


class DummyValidator:
    def validate_input(self, value: str, field_name: str = "input"):
        if "<" in value:
            return {"valid": False, "issues": ["xss"], "sanitized": value}
        return {"valid": True, "issues": [], "sanitized": value}


def test_event_callback_security():
    system = MasterCallbackSystem(security_validator=DummyValidator())
    results = []

    def cb(value):
        results.append(value)

    system.register_event_callback(CallbackEvent.ANALYSIS_START, cb, secure=True)
    # injection attempt should be blocked
    system.trigger_event(CallbackEvent.ANALYSIS_START, "<script>alert(1)</script>")
    assert results == []
    # safe call
    system.trigger_event(CallbackEvent.ANALYSIS_START, "hello")
    assert results == ["hello"]


def test_dash_callback_conflict():
    app = Dash(__name__)
    system = MasterCallbackSystem(app, security_validator=DummyValidator())

    @system.register_dash_callback(
        Output("o", "children"),
        Input("i", "value"),
        callback_id="c1",
        component_name="test",
    )
    def _cb(v):
        return v

    with pytest.raises(ValueError):
        @system.register_dash_callback(
            Output("o", "children"),
            Input("i2", "value"),
            callback_id="c2",
            component_name="test",
        )
        def _cb2(v):
            return v


