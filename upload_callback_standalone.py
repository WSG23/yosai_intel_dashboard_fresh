# Standalone callback registration that bypasses TrulyUnifiedCallbacks
from dash import callback, Input, Output, State
import dash_bootstrap_components as dbc

@callback(
    Output("upload-results-area", "children"),
    Input("working-file-upload", "contents"),
    State("working-file-upload", "filename"),
    prevent_initial_call=True
)
def handle_working_upload(contents, filenames):
    if contents:
        alerts = []
        if not isinstance(contents, list):
            filenames = [filenames] if filenames else ["unknown"]
        for filename in filenames:
            alerts.append(dbc.Alert(f"✅ File uploaded: {filename}", color="success"))
        return alerts
    return ""

print("✅ Upload callback registered outside TrulyUnifiedCallbacks")
