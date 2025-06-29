"""Utilities for processing uploaded files and creating previews."""
import base64
import io
import json
import logging
import re
from datetime import datetime
from typing import Any, Dict

from utils.unicode_handler import sanitize_unicode_input
from utils.file_validator import safe_decode_with_unicode_handling

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024
SAFE_FILENAME_RE = re.compile(r"^[A-Za-z0-9._\- ]{1,100}$")


def process_uploaded_file(contents: str, filename: str) -> Dict[str, Any]:
    """Process uploaded file content into a DataFrame."""
    try:
        filename = sanitize_unicode_input(filename)
        if not SAFE_FILENAME_RE.fullmatch(filename):
            return {
                "success": False,
                "error": "Invalid filename",
            }

        content_type, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        if len(decoded) > MAX_FILE_SIZE_BYTES:
            return {
                "success": False,
                "error": "File too large",
            }

        if filename.endswith(".csv"):
            text = safe_decode_with_unicode_handling(decoded, "utf-8")
            df = pd.read_csv(io.StringIO(text))
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
        elif filename.endswith(".json"):
            try:
                text = safe_decode_with_unicode_handling(decoded, "utf-8")
                json_data = json.loads(text)
                if isinstance(json_data, list):
                    df = pd.DataFrame(json_data)
                elif isinstance(json_data, dict):
                    if "data" in json_data:
                        df = pd.DataFrame(json_data["data"])
                    else:
                        df = pd.DataFrame([json_data])
                else:
                    return {"success": False, "error": f"Unsupported JSON structure: {type(json_data)}"}
            except json.JSONDecodeError as e:
                return {"success": False, "error": f"Invalid JSON format: {str(e)}"}
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
            "upload_time": datetime.now(),
        }
    except Exception as e:  # pragma: no cover - best effort
        return {"success": False, "error": f"Error processing file: {str(e)}"}


def create_file_preview(df: pd.DataFrame, filename: str) -> dbc.Card | dbc.Alert:
    """Create a preview card for an uploaded DataFrame."""
    try:
        num_rows, num_cols = df.shape

        column_info = []
        for col in df.columns[:10]:
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            column_info.append(f"{col} ({dtype}) - {null_count} nulls")

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
                            df.head(5),
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
