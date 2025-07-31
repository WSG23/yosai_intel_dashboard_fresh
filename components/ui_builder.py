from __future__ import annotations

import logging
from typing import Any, Dict

import dash.html as html
import dash_bootstrap_components as dbc
import pandas as pd

from components.file_preview import create_file_preview_ui
from file_processing import create_file_preview

logger = logging.getLogger(__name__)


class UploadUIBuilder:
    """Create UI elements for the upload workflow."""

    def build_success_alert(
        self,
        filename: str,
        rows: int,
        cols: int,
        prefix: str = "Successfully uploaded",
        processed: bool = True,
    ) -> dbc.Alert:
        details = f"📊 {rows:,} rows × {cols} columns"
        if processed:
            details += " processed"
        timestamp = pd.Timestamp.now().strftime("%H:%M:%S")
        return dbc.Alert(
            [
                html.H6(
                    [
                        html.I(
                            className="fas fa-check-circle me-2",
                            **{"aria-hidden": "true"},
                        ),
                        f"{prefix} {filename}",
                    ],
                    className="alert-heading",
                ),
                html.P(
                    [
                        details,
                        html.Br(),
                        html.Small(f"Processed at {timestamp}", className="text-muted"),
                    ]
                ),
            ],
            color="success",
            className="mb-3",
        )

    def build_failure_alert(self, message: str) -> dbc.Alert:
        return dbc.Alert(
            [
                html.H6("Upload Failed", className="alert-heading"),
                html.P(message),
            ],
            color="danger",
        )

    def build_file_preview_component(self, df: pd.DataFrame, filename: str) -> html.Div:
        preview_info = create_file_preview(df)
        return html.Div(
            [
                create_file_preview_ui(preview_info),
                dbc.Card(
                    [
                        dbc.CardHeader(
                            [html.H6("📋 Data Configuration", className="mb-0")]
                        ),
                        dbc.CardBody(
                            [
                                html.P(
                                    "Configure your data for analysis:",
                                    className="mb-3",
                                ),
                                dbc.ButtonGroup(
                                    [
                                        dbc.Button(
                                            "📋 Verify Columns",
                                            id="verify-columns-btn-simple",
                                            color="primary",
                                            size="sm",
                                        ),
                                        dbc.Button(
                                            "🤖 Classify Devices",
                                            id="classify-devices-btn",
                                            color="info",
                                            size="sm",
                                        ),
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

    def build_navigation(self) -> html.Div:
        return html.Div(
            [
                html.Hr(),
                html.H5("Ready for device analysis?"),
                dbc.Button(
                    "🚀 Start Device Analysis",
                    href="/device-analysis",
                    color="success",
                    size="lg",
                ),
            ]
        )

    def build_processing_stats(self, info: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        return {
            "total_files": len(info),
            "processed_files": len(info),
            "total_rows": sum(i.get("rows", 0) for i in info.values()),
            "total_columns": sum(i.get("columns", 0) for i in info.values()),
        }
