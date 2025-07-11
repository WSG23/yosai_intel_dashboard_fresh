import dash
import dash_bootstrap_components as dbc
from dash import dcc, html, Input, Output, callback

# Create app WITHOUT your app factory
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Minimal Upload Test"),
    dcc.Upload(
        id="test-upload",
        children="Drop files here",
        style={'border': '2px dashed blue', 'padding': '20px'}
    ),
    html.Div(id="test-output")
])

@callback(
    Output("test-output", "children"),
    Input("test-upload", "contents"),
    prevent_initial_call=True
)
def handle_test_upload(contents):
    return "File detected!" if contents else "No file"

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
