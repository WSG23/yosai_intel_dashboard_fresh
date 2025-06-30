"""Utilities for processing uploaded files and creating previews."""
import base64
import io
import json
import logging
from datetime import datetime
from typing import Any, Dict

from config.dynamic_config import dynamic_config
from security.file_validator import SecureFileValidator
from security.xss_validator import XSSPrevention

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)
_validator = SecureFileValidator()


def process_uploaded_file(contents: str, filename: str) -> Dict[str, Any]:
    """Process uploaded file content with enhanced size handling."""
    try:
        filename = _validator.sanitize_filename(filename)

        content_type, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)

        # Enhanced size validation with better error messages
        file_size_mb = len(decoded) / (1024 * 1024)
        max_size_mb = dynamic_config.get_max_upload_size_mb()
        max_size_bytes = dynamic_config.get_max_upload_size_bytes()

        if len(decoded) > max_size_bytes:
            return {
                "success": False,
                "error": f"File too large: {file_size_mb:.1f}MB exceeds limit of {max_size_mb}MB",
                "file_size_mb": file_size_mb,
                "max_allowed_mb": max_size_mb
            }

        if filename.endswith((".csv", ".xlsx", ".xls", ".json")):
            df = _validator.validate_file_contents(contents, filename)
        else:
            return {
                "success": False,
                "error": "Unsupported file type. Supported: .csv, .json, .xlsx, .xls",
            }

        if not isinstance(df, pd.DataFrame):
            return {"success": False, "error": f"Processing resulted in {type(df)} instead of DataFrame"}

        if df.empty:
            return {"success": False, "error": "File contains no data"}

        return {
            "success": True,
            "data": df,
            "rows": len(df),
            "columns": list(df.columns),
            "file_size_mb": file_size_mb,
            "upload_time": datetime.now(),
        }
    except Exception as e:
        logger.error(f"Error processing file {filename}: {e}")
        return {"success": False, "error": f"Error processing file: {str(e)}"}


def create_file_preview(df: pd.DataFrame, filename: str) -> dbc.Card | dbc.Alert:
    """Create a preview card for an uploaded DataFrame."""
    try:
        num_rows, num_cols = df.shape

        column_info = []
        for col in df.columns[:10]:
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            safe_col = XSSPrevention.sanitize_html_output(str(col))
            column_info.append(f"{safe_col} ({dtype}) - {null_count} nulls")

        preview_df = df.head(5).copy()
        preview_df.columns = [XSSPrevention.sanitize_html_output(str(c)) for c in preview_df.columns]
        preview_df = preview_df.applymap(lambda x: XSSPrevention.sanitize_html_output(str(x)))

        return dbc.Card(
            [
                dbc.CardHeader([html.H6(f"\U0001F4C4 {filename}", className="mb-0")]),
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6("File Statistics:", className="text-primary"),
                                        html.Ul(
                                            [
                                                html.Li(f"Rows: {num_rows:,}"),
                                                html.Li(f"Columns: {num_cols}"),
                                                html.Li(
                                                    f"Memory usage: {df.memory_usage(deep=True).sum() / 1024:.1f} KB"
                                                ),
                                            ]
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Columns:", className="text-primary"),
                                        html.Ul([html.Li(info) for info in column_info]),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                        html.Hr(),
                        html.H6("Sample Data:", className="text-primary mt-3"),
                        dbc.Table.from_dataframe(
                            preview_df,
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            size="sm",
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )
    except Exception as e:  # pragma: no cover - best effort
        logger.error(f"Error creating preview for {filename}: {e}")
        return dbc.Alert(f"Error creating preview: {str(e)}", color="warning")


__all__ = ["process_uploaded_file", "create_file_preview"]
