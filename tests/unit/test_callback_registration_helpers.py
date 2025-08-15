import pytest
import sys
import types

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


def test_validate_registration_normalizes_args():
    manager = make_manager()
    outs, ins, states, ins_arg, states_arg = manager._validate_registration(
        DummyIO("o", "children"), DummyIO("i", "value"), DummyIO("s", "data")
    )
    assert outs[0].component_id == "o"
    assert ins[0].component_id == "i"
    assert states[0].component_id == "s"
    assert ins_arg is not None
    assert states_arg is not None


def test_resolve_conflicts_duplicate_id():
    manager = make_manager()
    manager._dash_callbacks["cid"] = DashCallbackRegistration(
        callback_id="cid",
        component_name="comp",
        outputs=(),
        inputs=(),
        states=(),
    )
    with pytest.raises(ValueError):
        manager._resolve_conflicts("cid", (DummyIO("o", "children"),), False)


def test_wrap_callback_invokes_dash(monkeypatch):
    manager = make_manager()

    # Provide stub module to avoid importing heavy dependencies
    dummy_module = types.SimpleNamespace(wrap_callback=lambda f, o, s: f)
    sys.modules[
        "yosai_intel_dashboard.src.core.dash_callback_middleware"
    ] = dummy_module

    captured = {}

    def fake_callback(outputs, inputs, states, **kwargs):
        captured["args"] = (outputs, inputs, states, kwargs)

        def inner(func):
            captured["func"] = func
            return func

        return inner

    manager.app.callback = fake_callback  # type: ignore[assignment]

    def handler():
        return "ok"

    result = manager._wrap_callback(
        handler,
        DummyIO("o", "children"),
        None,
        tuple(),
        None,
        tuple(),
        (DummyIO("o", "children"),),
    )

    assert result is handler
    assert captured["func"] is handler
    assert captured["args"][0].component_id == "o"
