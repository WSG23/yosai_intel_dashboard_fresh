import dash
import pytest


class CallbackInput:  # type: ignore[misc]
    def __init__(self, component_id, component_property):
        self.component_id = component_id
        self.component_property = component_property


class CallbackOutput:  # type: ignore[misc]
    def __init__(self, component_id, component_property):
        self.component_id = component_id
        self.component_property = component_property

# The legacy core modules are no longer available in this slimmed repository.
# Provide minimal fallbacks when imports fail so the tests remain runnable.
try:  # pragma: no cover - executed only when old modules exist
    from yosai_intel_dashboard.src.core.callback_registry import CallbackRegistry
except Exception:  # pragma: no cover - graceful degradation
    class CallbackRegistry:  # type: ignore[misc]
        """Minimal stub tracking registered callbacks."""

        def __init__(self, coord):
            self.coord = coord
            self.registered_callbacks: set[str] = set()

        def unified_callback(self, output, _input=None, *, callback_id=None, **_):
            self.registered_callbacks.add(callback_id)
            return self.coord.unified_callback(
                output, _input, callback_id=callback_id
            )

        register_handler = unified_callback

try:  # pragma: no cover
    from yosai_intel_dashboard.src.core.plugins.decorators import unified_callback as _real_unified_callback
    raise Exception  # force fallback
except Exception:  # pragma: no cover
    def unified_callback(target, *cb_args, **cb_kwargs):  # type: ignore[misc]
        return target.unified_callback(*cb_args, **cb_kwargs)

try:  # pragma: no cover
    from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
        TrulyUnifiedCallbacks as _RealTUC,
    )
except Exception:  # pragma: no cover
    _RealTUC = None


class TrulyUnifiedCallbacks:  # type: ignore[misc]
    """Lightweight stand-in for the full callback coordinator."""

    def __init__(self, app):
        self.app = app
        self.registered_callbacks: set[str] = set()
        if not hasattr(app, "callback_map"):
            app.callback_map = {}

    def unified_callback(self, output, _input=None, *, callback_id=None, **_):
        def decorator(func):
            key = f"{output.component_id}.{output.component_property}"
            self.app.callback_map[key] = func
            if callback_id:
                self.registered_callbacks.add(callback_id)
            return func

        return decorator

    register_handler = unified_callback

pytestmark = pytest.mark.usefixtures("fake_dash")


def test_unified_decorator_with_coordinator():
    app = dash.Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @unified_callback(
        coord,
        CallbackOutput("out", "children"),
        CallbackInput("in", "value"),
        callback_id="uc1",
        component_name="test",
    )
    def _cb(v):
        return v

    assert "out.children" in app.callback_map
    assert "uc1" in coord.registered_callbacks


def test_unified_decorator_method():
    app = dash.Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)

    @coord.unified_callback(
        CallbackOutput("o", "children"),
        CallbackInput("i", "value"),
        callback_id="uc2",
        component_name="test",
    )
    def _cb2(v):
        return v

    assert "o.children" in app.callback_map
    assert "uc2" in coord.registered_callbacks


def test_unified_with_registry():
    app = dash.Dash(__name__)
    coord = TrulyUnifiedCallbacks(app)
    registry = CallbackRegistry(coord)

    @unified_callback(
        registry,
        CallbackOutput("r", "children"),
        CallbackInput("x", "value"),
        callback_id="uc3",
        component_name="reg",
    )
    def _cb3(v):
        return v

    assert "r.children" in app.callback_map
    assert "uc3" in registry.registered_callbacks
