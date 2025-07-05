"""FileProcessor for reading and validating uploaded files."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Optional, List, Tuple, Dict
from datetime import datetime

import dash_bootstrap_components as dbc
from dash import html
from security.xss_validator import XSSPrevention
import logging

import pandas as pd

from services.input_validator import ValidationResult
from security.dataframe_validator import DataFrameSecurityValidator
from services.data_processing.unified_file_validator import UnifiedFileValidator as CoreValidator
from core.exceptions import ValidationError
from .file_handler import process_file_simple
from .core.exceptions import FileProcessingError

logger = logging.getLogger(__name__)


class FileProcessorValidator:
    """Combine file and DataFrame validation helpers."""

    def __init__(self, max_size_mb: Optional[int] = None) -> None:
        self.core_validator = CoreValidator(max_size_mb)
        self.df_validator = DataFrameSecurityValidator()

    # ------------------------------------------------------------------
    # Basic helpers
    # ------------------------------------------------------------------
    def validate_path(self, path: Path) -> None:
        result = self.core_validator.validate_file_upload(path)
        if not result.valid:
            raise ValidationError(result.message)

    def _read_path(self, path: Path) -> pd.DataFrame:
        if path.suffix.lower() == ".csv":
            df = pd.read_csv(path)
        elif path.suffix.lower() == ".json":
            with open(path, "r", encoding="utf-8", errors="replace") as f:
                data = json.load(f)
            df = pd.DataFrame(data)
        elif path.suffix.lower() in {".xlsx", ".xls"}:
            df = pd.read_excel(path)
        else:
            raise ValidationError(f"Unsupported file type: {path.suffix}")
        return df

    def load_dataframe(self, path: Path) -> pd.DataFrame:
        self.validate_path(path)
        df = self._read_path(path)
        df = self.df_validator.validate_for_upload(df)
        return df

    def validate_contents(self, contents: str, filename: str) -> pd.DataFrame:
        df = self.core_validator.validate_file(contents, filename)
        result = self.core_validator.validate_file_upload(df)
        if not result.valid:
            raise ValidationError(result.message)
        df = self.df_validator.validate_for_upload(df)
        return df


class FileProcessor:
    """High level processor that delegates to :class:`FileProcessorValidator`."""

    def __init__(self, validator: Optional[FileProcessorValidator] = None) -> None:
        self.validator = validator or FileProcessorValidator()

    def process_path(self, file_path: str | Path) -> pd.DataFrame:
        path = Path(file_path)
        logger.info("Processing file %s", path)
        return self.validator.load_dataframe(path)

    def process_uploaded_contents(self, contents: str, filename: str) -> pd.DataFrame:
        logger.info("Processing uploaded contents for %s", filename)
        return self.validator.validate_contents(contents, filename)

    def process_files(self, file_paths: List[str]) -> Tuple[pd.DataFrame, List[str], int, int]:
        """Load and validate a list of files."""
        all_data: List[pd.DataFrame] = []
        info: List[str] = []
        total_records = 0
        processed_files = 0

        for path in file_paths:
            try:
                df = self.validator.load_dataframe(Path(path))
                df["source_file"] = path
                all_data.append(df)
                total_records += len(df)
                processed_files += 1
                info.append(f"✅ {path}: {len(df)} records")
            except Exception as exc:  # pragma: no cover - best effort
                info.append(f"❌ {path}: {exc}")
                logger.error("Exception processing %s: %s", path, exc)

        combined = pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        return combined, info, processed_files, total_records

    def read_uploaded_file(self, contents: str, filename: str) -> tuple[pd.DataFrame, float]:
        """Decode ``contents`` and return the dataframe and raw size in MB."""
        import base64
        import io
        from config.dynamic_config import dynamic_config

        sanitized = self.validator.core_validator.sanitize_filename(filename)
        if "," not in contents:
            raise ValidationError("Invalid upload data")
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        file_size_mb = len(decoded) / (1024 * 1024)

        if len(decoded) > dynamic_config.get_max_upload_size_bytes():
            raise ValidationError(
                f"File too large: {file_size_mb:.1f}MB exceeds limit of {dynamic_config.get_max_upload_size_mb()}MB"
            )

        stream = io.BytesIO(decoded)
        name = sanitized.lower()
        chunk_size = getattr(dynamic_config.analytics, "chunk_size", 50000)

        if name.endswith(".csv"):
            chunks = []
            header = None
            for chunk in pd.read_csv(stream, chunksize=chunk_size, encoding="utf-8"):
                if header is None:
                    header = list(chunk.columns)
                dup = (chunk.astype(str) == header).all(axis=1)
                chunk = chunk[~dup]
                chunks.append(chunk)
            df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
        elif name.endswith(".json"):
            try:
                chunks = []
                for chunk in pd.read_json(stream, lines=True, chunksize=chunk_size):
                    chunks.append(chunk)
                df = pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()
            except ValueError:
                stream.seek(0)
                df = pd.read_json(stream)
        elif name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(stream)
        else:
            raise ValidationError("Unsupported file type. Supported: .csv, .json, .xlsx, .xls")

        return df, file_size_mb

    def health_check(self) -> dict[str, Any]:
        return {"status": "ok"}


_processor = FileProcessor()


def process_uploaded_file(contents: str, filename: str) -> Dict[str, Any]:
    """Process uploaded file content using the shared processor."""
    try:
        df, file_size_mb = _processor.read_uploaded_file(contents, filename)

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
    except Exception as e:  # pragma: no cover - best effort
        logger.error("Error processing file %s: %s", filename, e)
        return {"success": False, "error": f"Error processing file: {str(e)}"}


def create_file_preview(df: pd.DataFrame, filename: str) -> dbc.Card | dbc.Alert:
    """Create a preview card showing the correct row count."""
    try:
        actual_rows, actual_cols = df.shape
        df = df.head(99)
        preview_rows = min(5, actual_rows)

        logger.info(
            "Creating preview for %s: %d rows \u00d7 %d columns",
            filename,
            actual_rows,
            actual_cols,
        )

        column_info = []
        for col in df.columns[:10]:
            dtype = str(df[col].dtype)
            null_count = df[col].isnull().sum()
            safe_col = XSSPrevention.sanitize_html_output(str(col))
            column_info.append(f"{safe_col} ({dtype}) - {null_count} nulls")

        preview_df: pd.DataFrame = df.head(preview_rows).copy()
        preview_df.columns = [
            XSSPrevention.sanitize_html_output(str(c)) for c in preview_df.columns
        ]

        def _sanitize(value: Any) -> str:
            return XSSPrevention.sanitize_html_output(str(value))

        preview_df = preview_df.map(_sanitize)

        if actual_rows <= 10:
            status_color = "warning"
            status_message = f"\u26A0\ufe0f Only {actual_rows} rows found - check if file is complete"
        else:
            status_color = "success"
            status_message = f"\u2705 Successfully loaded {actual_rows:,} rows"

        return dbc.Card(
            [
                dbc.CardHeader(
                    [
                        html.H6(f"\ud83d\udcc4 {filename}", className="mb-0"),
                        dbc.Badge(
                            f"{actual_rows:,} rows total",
                            color="info",
                            className="ms-2",
                        ),
                    ]
                ),
                dbc.CardBody(
                    [
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
                                                html.Li("Status: Complete"),
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
                        html.H6(
                            f"Sample Data (first {preview_rows} rows):",
                            className="text-primary mt-3",
                        ),
                        dbc.Table.from_dataframe(
                            preview_df,
                            striped=True,
                            bordered=True,
                            hover=True,
                            responsive=True,
                            size="sm",
                        ),
                        dbc.Alert(
                            f"\ud83d\udcca Processing Summary: {actual_rows:,} rows will be available for analytics. "
                            f"Above table shows first {preview_rows} rows for preview only.",
                            color="info",
                            className="mt-3",
                        ),
                    ]
                ),
            ],
            className="mb-3",
        )
    except Exception as e:  # pragma: no cover - best effort
        logger.error("Error creating preview for %s: %s", filename, e)
        return dbc.Alert(f"Error creating preview: {str(e)}", color="warning")


__all__ = [
    "FileProcessor",
    "FileProcessorValidator",
    "process_file_simple",
    "FileProcessingError",
    "process_uploaded_file",
    "create_file_preview",
]
