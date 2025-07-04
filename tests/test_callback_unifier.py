from dash.dependencies import Output, Input
from dash import Dash

from core.callback_manager import CallbackManager
from core.callback_events import CallbackEvent
from core.callback_migration import UnifiedCallbackCoordinatorWrapper


def test_event_registration_delegates():
    app = Dash(__name__)
    manager = CallbackManager()
    wrapper = UnifiedCallbackCoordinatorWrapper(app, manager)

    called = []

    def handler(value):
        called.append(value)

    wrapper.register_event(CallbackEvent.ANALYSIS_START, handler, priority=5)
    manager.trigger(CallbackEvent.ANALYSIS_START, 1)

    assert called == [1]


def test_callback_registration():
    app = Dash(__name__)
    manager = CallbackManager()
    wrapper = UnifiedCallbackCoordinatorWrapper(app, manager)

    @wrapper.register_callback(
        Output("out", "children"),
        Input("in", "value"),
        callback_id="cb",
        component_name="test",
    )
    def cb(v):
        return v

    assert "out.children" in app.callback_map
    assert "cb" in wrapper.registered_callbacks
