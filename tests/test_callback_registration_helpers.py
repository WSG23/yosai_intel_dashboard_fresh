import pytest
import sys
import types
from typing import Any

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    DashCallbackRegistration,
    TrulyUnifiedCallbacks,
)


class DummyIO:
    def __init__(self, component_id: str, component_property: str, allow_duplicate: bool = False):
        self.component_id = component_id
        self.component_property = component_property
        self.allow_duplicate = allow_duplicate


class DummyDash:
    def callback(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


def make_manager() -> TrulyUnifiedCallbacks:
    return TrulyUnifiedCallbacks(DummyDash(), security_validator=object())


def test_validate_registration_normalizes_args_and_duplicate_id():
    manager = make_manager()
    outs, ins, states, ins_arg, states_arg = manager._validate_registration(
        "cid", DummyIO("o", "children"), DummyIO("i", "value"), DummyIO("s", "data")
    )
    assert outs[0].component_id == "o"
    assert ins[0].component_id == "i"
    assert states[0].component_id == "s"
    assert ins_arg is not None
    assert states_arg is not None

    manager._dash_callbacks["cid"] = DashCallbackRegistration(
        callback_id="cid",
        component_name="comp",
        outputs=(),
        inputs=(),
        states=(),
    )
    with pytest.raises(ValueError):
        manager._validate_registration("cid", DummyIO("o", "c"), None, None)


def test_wrap_callback_invokes_dash(monkeypatch):
    manager = make_manager()

    captured = {}

    # Provide stub module to capture wrap_callback usage
    def fake_wrap(func, outputs, security):
        captured["func"] = func
        captured["outputs"] = outputs
        captured["security"] = security
        return func

    dummy_module = types.SimpleNamespace(wrap_callback=fake_wrap)
    sys.modules[
        "yosai_intel_dashboard.src.core.dash_callback_middleware"
    ] = dummy_module

    def handler():
        return "ok"

    result = manager._wrap_callback(handler, (DummyIO("o", "children"),))

    assert result is handler
    assert captured["func"] is handler
    assert captured["outputs"][0].component_id == "o"


def test_handle_register_registers_callback(monkeypatch):
    manager = make_manager()

    wrapped_calls: dict[str, Any] = {}

    def fake_wrap(func, outputs_tuple):
        wrapped_calls["func"] = func
        wrapped_calls["outputs"] = outputs_tuple
        return func

    monkeypatch.setattr(manager, "_wrap_callback", fake_wrap)

    outputs = DummyIO("o", "children")
    decorator = manager.handle_register(
        outputs, callback_id="cid", component_name="comp"
    )

    def handler() -> str:
        return "ok"

    result = decorator(handler)

    assert wrapped_calls["func"] is handler
    assert manager._dash_callbacks["cid"].outputs[0].component_id == "o"
    assert manager._output_map["o.children"] == "cid"
    assert manager._namespaces["comp"] == ["cid"]
    assert result is handler
