from dash import Input, Output, dcc, html

from core.app_factory import create_app
from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from ui_callback_controller import UIEvent, ui_callback_controller

# Create app using YOUR app factory
app = create_app()
callbacks = TrulyUnifiedCallbacks(app)


# Override the upload page using TrulyUnifiedCallbacks
@callbacks.handle_register(
    Output("page-content", "children"),
    Input("url", "pathname"),
    callback_id="factory_router",
    component_name="app_factory",
    prevent_initial_call=True,
)
def simple_router(pathname):
    if pathname == "/upload":
        return html.Div(
            [
                html.H1("App Factory Upload Test"),
                dcc.Upload(
                    id="factory-upload",
                    children="Drop files here (via app factory)",
                    style={"border": "2px dashed green", "padding": "20px"},
                ),
                html.Div("Ready", id="factory-output"),
            ]
        )
    return html.Div(f"Page: {pathname}")


# Simple callback using TrulyUnifiedCallbacks
@callbacks.handle_register(
    Output("factory-output", "children"),
    Input("factory-upload", "contents"),
    callback_id="factory_upload",
    component_name="app_factory",
    prevent_initial_call=True,
)
def handle_factory_upload(contents):
    ui_callback_controller.trigger(UIEvent.UI_UPDATE, "upload", {})
    return "File detected via app factory!" if contents else "No file"


if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
