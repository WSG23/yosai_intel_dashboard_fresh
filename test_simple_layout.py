import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.H1("🏯 Simple Yōsai Test"),
    html.P("If you see this properly, the issue is in _create_navbar or page_container"),
    dcc.Store(id="global-store", data={})
])

if __name__ == "__main__":
    app.run_server(debug=True, port=8052)
