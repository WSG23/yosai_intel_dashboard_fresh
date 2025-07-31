from __future__ import annotations

"""Callbacks for the data enhancer feature."""

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, dash_table, dcc, html
from dash.exceptions import PreventUpdate

from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import TrulyUnifiedCallbacks
from services.data_enhancer.processor import DataEnhancerProcessor


def register_callbacks(app, container) -> None:
    """Register data enhancer callbacks."""
    callbacks = TrulyUnifiedCallbacks(app)
    _register(callbacks)


def _register(cb: TrulyUnifiedCallbacks) -> None:
    """Group all callbacks for easier testing."""
    processor = DataEnhancerProcessor()

    @cb.callback(
        Output("uploaded-data", "data"),
        Output("upload-status", "children"),
        Output("data-preview", "children"),
        Input("upload-input", "contents"),
        State("upload-input", "filename"),
        prevent_initial_call=True,
        callback_id="de-upload",
        component_name="data_enhancer",
    )
    def handle_upload(contents: str | None, filename: str | None):
        """Decode uploaded file and show a preview."""
        if not contents or not filename:
            raise PreventUpdate
        df, msg = processor.decode_contents(contents, filename)
        if df is None:
            return None, dbc.Alert(msg, color="danger"), ""
        preview = dash_table.DataTable(
            data=df.head().to_dict("records"),
            columns=[{"name": c, "id": c} for c in df.columns],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "fontSize": "12px"},
        )
        return (
            df.to_json(date_format="iso", orient="split"),
            dbc.Alert(msg, color="success"),
            preview,
        )

    @cb.callback(
        Output("column-suggestions", "data"),
        Output("ai-status", "children"),
        Input("suggest-columns-btn", "n_clicks"),
        State("uploaded-data", "data"),
        prevent_initial_call=True,
        callback_id="de-column-suggest",
        component_name="data_enhancer",
    )
    def suggest_columns(n_clicks: int | None, data: str | None):
        """Generate column suggestions from uploaded data."""
        if not n_clicks or not data:
            raise PreventUpdate
        df = pd.read_json(data, orient="split")
        suggestions = processor.get_column_suggestions(df)
        status = dbc.Alert(f"Found {len(suggestions)} suggestions", color="info")
        return suggestions, status

    @cb.callback(
        Output("enhanced-data", "data"),
        Output("enhance-status", "children"),
        Output("enhanced-preview", "children"),
        Input("enhance-btn", "n_clicks"),
        State("uploaded-data", "data"),
        State("column-mapping-store", "data"),
        prevent_initial_call=True,
        callback_id="de-enhance",
        component_name="data_enhancer",
    )
    def enhance_data(n_clicks: int | None, data: str | None, mappings: dict | None):
        """Apply column mappings and store enhanced data."""
        if not n_clicks or not data:
            raise PreventUpdate
        df = pd.read_json(data, orient="split")
        enhanced = processor.apply_column_mappings(df, mappings or {})
        preview = dash_table.DataTable(
            data=enhanced.head().to_dict("records"),
            columns=[{"name": c, "id": c} for c in enhanced.columns],
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "left", "fontSize": "12px"},
        )
        status = dbc.Alert("Data enhancement complete", color="success")
        return (
            enhanced.to_json(date_format="iso", orient="split"),
            status,
            preview,
        )

    @cb.callback(
        Output("download-enhanced", "data"),
        Input("download-btn", "n_clicks"),
        State("enhanced-data", "data"),
        prevent_initial_call=True,
        callback_id="de-download",
        component_name="data_enhancer",
    )
    def download_enhanced(n_clicks: int | None, data: str | None):
        """Provide CSV download for the enhanced dataset."""
        if not n_clicks or not data:
            raise PreventUpdate
        df = pd.read_json(data, orient="split")
        return dcc.send_data_frame(df.to_csv, "enhanced.csv", index=False)
