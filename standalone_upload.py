#!/usr/bin/env python3
"""
Standalone upload app with proper styling.
"""
import dash
from dash import dcc, html, Input, Output, callback
import dash_bootstrap_components as dbc

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H2("File Upload", className="text-center mb-4"),
            
            dcc.Upload(
                id="upload",
                children=html.Div([
                    html.I(className="fas fa-cloud-upload-alt fa-2x mb-2", **{"aria-hidden": "true"}),
                    html.Br(),
                    "Drag and drop files here or click to browse"
                ]),
                style={
                    'width': '100%', 'height': '120px', 'lineHeight': '120px',
                    'borderWidth': '2px', 'borderStyle': 'dashed', 'borderRadius': '8px',
                    'textAlign': 'center', 'border': '2px dashed #000000',  # BLACK
                    'backgroundColor': '#f8f9fa', 'cursor': 'pointer'
                },
                multiple=True
            ),
            
            html.Div(id="output", className="mt-3")
        ], width=6)
    ], justify="center")
])

@callback(Output("output", "children"), Input("upload", "contents"), Input("upload", "filename"))
def upload_file(contents, filenames):
    if contents:
        alerts = []
        if not isinstance(contents, list):
            filenames = [filenames]
        for filename in filenames:
            alerts.append(dbc.Alert(f"✅ Uploaded: {filename}", color="success"))
        return alerts
    return ""

if __name__ == "__main__":
    app.run_server(debug=True, port=8060)
