#!/usr/bin/env python3
"""Standalone preview for the UploadArea component."""

import dash
import dash_bootstrap_components as dbc
from dash import dcc, html

from components.upload import UploadArea
from core.truly_unified_callbacks import TrulyUnifiedCallbacks

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
callbacks = TrulyUnifiedCallbacks(app)
upload = UploadArea()

app.layout = dbc.Container(
    [
        html.H2("UploadArea preview", className="my-3"),
        upload.render(),
    ],
    fluid=True,
)


@callbacks.callback(
    dash.Output(upload.results_id, "children"),
    dash.Input(upload.upload_id, "contents"),
    dash.State(upload.upload_id, "filename"),
    prevent_initial_call=True,
    callback_id="display_upload",
    component_name="upload_area_app",
)
def _display_upload(contents, names):
    if contents is None:
        raise dash.exceptions.PreventUpdate
    if isinstance(names, list):
        names = ", ".join(names)
    return html.Div([html.P(f"Uploaded: {names}")])


if __name__ == "__main__":
    app.run_server(debug=True)
