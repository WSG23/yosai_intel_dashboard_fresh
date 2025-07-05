"""Utilities for processing uploaded files and creating previews."""

import base64
import io
import logging
from datetime import datetime
from typing import Any, Dict

from config.dynamic_config import dynamic_config
from services.data_processing.unified_file_validator import UnifiedFileValidator
from security.xss_validator import XSSPrevention
from services.data_validation import DataValidationService
from services.analytics import map_and_clean

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html

logger = logging.getLogger(__name__)
_handler = UnifiedFileValidator()


def process_uploaded_file(contents: str, filename: str) -> Dict[str, Any]:
    """Process uploaded file content with enhanced size handling."""
    try:
        filename = _handler.sanitize_filename(filename)

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
                "max_allowed_mb": max_size_mb,
            }

        validator = DataValidationService()

        if filename.lower().endswith(".csv"):
            chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)
            stream = io.BytesIO(decoded)
            header = None
            chunks = []
            for chunk in pd.read_csv(stream, chunksize=chunk_size, encoding="utf-8"):
                if header is None:
                    header = list(chunk.columns)
                duplicate = (chunk.astype(str) == header).all(axis=1)
                chunk = chunk[~duplicate]
                chunk = validator.validate(chunk)
                chunk = map_and_clean(chunk)
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        elif filename.lower().endswith(".json"):
            chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)
            stream = io.BytesIO(decoded)
            try:
                chunks = []
                for chunk in pd.read_json(stream, lines=True, chunksize=chunk_size):
                    chunk = validator.validate(chunk)
                    chunks.append(map_and_clean(chunk))
                df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
            except ValueError:
                stream.seek(0)
                df = pd.read_json(stream)
                df = map_and_clean(validator.validate(df))
        elif filename.lower().endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
            df = map_and_clean(validator.validate(df))
        else:
            return {
                "success": False,
                "error": "Unsupported file type. Supported: .csv, .json, .xlsx, .xls",
            }

        if not isinstance(df, pd.DataFrame):
            return {
                "success": False,
                "error": f"Processing resulted in {type(df)} instead of DataFrame",
            }

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
    """Create a preview card showing the correct row count.

    The preview table uses ``df.head(5)`` and clamps ``df`` to fewer than
    100 rows before rendering.
    """
    try:
        # CRITICAL: Get actual DataFrame size
        actual_rows, actual_cols = df.shape
        df = df.head(99)
        preview_rows = min(5, actual_rows)  # Only for table display

        logger.info(
            f"Creating preview for {filename}: {actual_rows} rows × {actual_cols} columns"
        )

        column_info = []
        for col in df.columns[:10]:
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            safe_col = XSSPrevention.sanitize_html_output(str(col))
            column_info.append(f"{safe_col} ({dtype}) - {null_count} nulls")

        # Display sample (but show actual count in stats)
        preview_df: pd.DataFrame = df.head(preview_rows).copy()
        preview_df.columns = [
            XSSPrevention.sanitize_html_output(str(c)) for c in preview_df.columns
        ]

        def _sanitize(value: Any) -> str:
            return XSSPrevention.sanitize_html_output(str(value))

        preview_df = preview_df.map(_sanitize)

        # Display status messaging based on file size
        if actual_rows <= 10:
            status_color = "warning"
            status_message = (
                f"⚠️ Only {actual_rows} rows found - check if file is complete"
            )
        else:
            status_color = "success"
            status_message = f"✅ Successfully loaded {actual_rows:,} rows"

        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H6(f"📄 {filename}", className="mb-0"),
                        dbc.Badge(
                            f"{actual_rows:,} rows total",
                            color="info",
                            className="ms-2",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
                        # CRITICAL: Show actual processing status
                        dbc.Alert(status_message, color=status_color, className="mb-3"),
                        dbc.Row(
                            [
                                dbc.Col(
                                    [
                                        html.H6(
                                            "Processing Statistics:",
                                            className="text-primary",
                                        ),
                                        html.Ul(
                                            [
                                                html.Li(f"Total Rows: {actual_rows:,}"),
                                                html.Li(f"Columns: {actual_cols}"),
                                                html.Li(
                                                    f"Memory: {df.memory_usage(deep=True).sum() / (1024 * 1024):,.1f} MB"
                                                ),
                                                html.Li(f"Status: Complete"),
                                            ]
                                        ),
                                    ],
                                    width=6,
                                ),
                                dbc.Col(
                                    [
                                        html.H6("Columns:", className="text-primary"),
                                        html.Ul(
                                            [html.Li(info) for info in column_info]
                                        ),
                                    ],
                                    width=6,
                                ),
                            ]
                        ),
                        html.Hr(),
                        html.H6(
                            f"Sample Data (first {preview_rows} rows):",
                            className="text-primary mt-3",
                        ),
                        dbc.Table.from_dataframe(  # pyright: ignore[reportAttributeAccessIssue]
                            preview_df,
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            size="sm",
                        ),
                        # ADDITIONAL: Clear indication of processing vs display
                        dbc.Alert(
                            f"📊 Processing Summary: {actual_rows:,} rows will be available for analytics. "
                            f"Above table shows first {preview_rows} rows for preview only.",
                            color="info",
                            className="mt-3",
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )
    except Exception as e:
        logger.error(f"Error creating preview for {filename}: {e}")
        return dbc.Alert(f"Error creating preview: {str(e)}", color="warning")


__all__ = ["process_uploaded_file", "create_file_preview"]
