import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from components.ui.navbar import create_navbar_layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Force the exact same layout structure
app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Nav(
        create_navbar_layout(),
        className="top-panel",
    ),
    html.Main([
        html.H1("🏯 Testing Direct Layout"),
        html.P("This should show proper webpage with logo and nav")
    ], id="page-content", className="main-content p-4"),
    dcc.Store(id="global-store", data={}),
])

if __name__ == "__main__":
    app.run_server(debug=True, port=8053)
