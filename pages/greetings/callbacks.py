from dash import Input, Output
from dash.exceptions import PreventUpdate

try:  # pragma: no cover - allow tests without full core package
    from core.truly_unified_callbacks import TrulyUnifiedCallbacks
except Exception:  # pragma: no cover - lightweight fallback
    class TrulyUnifiedCallbacks:  # type: ignore[too-few-public-methods]
        """Minimal stub used when core package isn't available."""

        def __init__(self, app=None):
            self.app = app

        def callback(self, *args, **kwargs):
            def decorator(func):
                if self.app is not None:
                    return self.app.callback(*args, **kwargs)(func)
                return func

            return decorator

        register_handler = callback
from services.greeting import GreetingService
from simple_di import inject


def register_callbacks(app, container) -> None:
    """Register page callbacks."""

    callbacks = TrulyUnifiedCallbacks(app)

    @callbacks.callback(
        Output("greet-output", "children"),
        Input("name-input", "value"),
        callback_id="greet",
        component_name="greetings",
    )
    @inject(container=container)
    def _update_greeting(name: str, svc: GreetingService):
        if not name:
            raise PreventUpdate
        return svc.greet(name)

    return None
