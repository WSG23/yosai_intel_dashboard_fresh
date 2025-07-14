import dash
from dash import html, dcc
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    html.H1("Test Layout"),
    html.P("If you see this as proper HTML, the issue is in app_factory")
])

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
