from dash import Input, Output
from dash.exceptions import PreventUpdate

from services.greeting import GreetingService
from simple_di import inject


def register_callbacks(app, container) -> None:
    """Register page callbacks."""

    @app.callback(Output("greet-output", "children"), Input("name-input", "value"))
    @inject(container=container)
    def _update_greeting(name: str, svc: GreetingService):
        if not name:
            raise PreventUpdate
        return svc.greet(name)

    return None
