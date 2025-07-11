from core.app_factory import create_app
from dash import html, dcc, Input, Output

# Create app using YOUR app factory
app = create_app()

# Override the upload page to bypass TrulyUnifiedCallbacks
@app.callback(
    Output("page-content", "children"),
    Input("url", "pathname"),
    prevent_initial_call=True
)
def simple_router(pathname):
    if pathname == "/upload":
        return html.Div([
            html.H1("App Factory Upload Test"),
            dcc.Upload(
                id="factory-upload",
                children="Drop files here (via app factory)",
                style={'border': '2px dashed green', 'padding': '20px'}
            ),
            html.Div("Ready", id="factory-output")
        ])
    return html.Div(f"Page: {pathname}")

# Simple callback using standard Dash (not TrulyUnifiedCallbacks)
@app.callback(
    Output("factory-output", "children"),
    Input("factory-upload", "contents"),
    prevent_initial_call=True
)
def handle_factory_upload(contents):
    return "File detected via app factory!" if contents else "No file"

if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
