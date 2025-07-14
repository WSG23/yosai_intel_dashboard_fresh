import dash
from dash import html, dcc, Input, Output, callback
import dash_bootstrap_components as dbc
from components.ui.navbar import create_navbar_layout

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div([
    dcc.Location(id="url", refresh=False),
    html.Nav(create_navbar_layout(), className="top-panel"),
    html.Main(id="page-content", className="main-content p-4"),
    dcc.Store(id="global-store", data={}),
])

@app.callback(Output("page-content", "children"), Input("url", "pathname"))
def display_page(pathname):
    if pathname == "/analytics":
        return html.H1("📊 Analytics Page")
    elif pathname == "/graphs": 
        return html.H1("📈 Graphs Page")
    elif pathname == "/upload":
        return html.H1("📤 Upload Page")
    elif pathname == "/export":
        return html.H1("📥 Export Page") 
    elif pathname == "/settings":
        return html.H1("⚙️ Settings Page")
    elif pathname == "/dashboard":
        return html.H1("🏠 Dashboard")
    else:
        return html.H1("🏠 Welcome to Yōsai Dashboard")

if __name__ == "__main__":
    app.run_server(debug=True, port=8054)
