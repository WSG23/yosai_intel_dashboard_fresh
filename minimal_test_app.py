import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

print("Creating minimal test app...")

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id="url"),
    html.H1("🧪 Minimal Test"),
    html.Div(id="content", children="Basic content works"),
])

@app.callback(
    dash.Output("content", "children"),
    dash.Input("url", "pathname")
)
def update_content(pathname):
    return f"Page: {pathname or '/'}"

if __name__ == '__main__':
    print("Starting minimal test server...")
    app.run_server(debug=True, port=8051)
