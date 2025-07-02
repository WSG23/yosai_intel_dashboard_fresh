import logging
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
from dash import html
import dash_bootstrap_components as dbc

from services.upload_service import create_file_preview
from utils.upload_store import uploaded_data_store as _uploaded_data_store
from services.ai_suggestions import generate_column_suggestions

logger = logging.getLogger(__name__)


def build_success_alert(filename: str, rows: int, cols: int, *, prefix: str = "Successfully uploaded", processed: bool = True) -> dbc.Alert:
    """Return a Bootstrap alert indicating a successful upload."""
    details = f"📊 {rows:,} rows × {cols} columns"
    if processed:
        details += " processed"
    timestamp = datetime.now().strftime("%H:%M:%S")
    return dbc.Alert(
        [
            html.H6([
                html.I(className="fas fa-check-circle me-2"), f"{prefix} {filename}"
            ], className="alert-heading"),
            html.P([details, html.Br(), html.Small(f"Processed at {timestamp}", className="text-muted")])
        ],
        color="success",
        className="mb-3",
    )


def build_failure_alert(message: str) -> dbc.Alert:
    """Return a Bootstrap alert for a failed file upload."""
    return dbc.Alert(
        [html.H6("Upload Failed", className="alert-heading"), html.P(message)],
        color="danger",
    )


def build_file_preview_component(df: pd.DataFrame, filename: str) -> html.Div:
    """Return a preview card and configuration buttons for an uploaded file."""
    return html.Div(
        [
            create_file_preview(df, filename),
            dbc.Card(
                [
                    dbc.CardHeader([html.H6("📋 Data Configuration", className="mb-0")]),
                    dbc.CardBody(
                        [
                            html.P("Configure your data for analysis:", className="mb-3"),
                            dbc.ButtonGroup(
                                [
                                    dbc.Button("📋 Verify Columns", id="verify-columns-btn-simple", color="primary", size="sm"),
                                    dbc.Button("🤖 Classify Devices", id="classify-devices-btn", color="info", size="sm"),
                                ],
                                className="w-100",
                            ),
                        ]
                    ),
                ],
                className="mb-3",
            ),
        ]
    )


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Return all uploaded data frames."""
    return _uploaded_data_store.get_all_data()


def get_uploaded_filenames() -> List[str]:
    """Return a list of uploaded file names."""
    return _uploaded_data_store.get_filenames()


def clear_uploaded_data() -> None:
    """Clear all uploaded data from the store."""
    _uploaded_data_store.clear_all()
    logger.info("Uploaded data cleared")


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Return stored file information."""
    return _uploaded_data_store.get_file_info()


__all__ = [
    "build_success_alert",
    "build_failure_alert",
    "build_file_preview_component",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
]
