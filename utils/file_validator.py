"""
Enhanced file validator with robust Unicode handling and security checks.
Replaces utils/file_validator.py with modular, testable components.
"""

from __future__ import annotations

import base64
import io
import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import pandas as pd

from core.unicode import UnicodeProcessor

logger = logging.getLogger(__name__)


class FileValidationError(Exception):
    """Base exception for file validation errors."""


class SecurityValidationError(FileValidationError):
    """Raised when file fails security validation."""


class FileContentValidator:
    """Comprehensive file content validation with security checks."""

    SUPPORTED_TYPES = {
        ".csv": {
            "mime_types": ["text/csv", "application/csv", "text/plain"],
            "max_size": 100 * 1024 * 1024,  # 100MB
        },
        ".json": {
            "mime_types": ["application/json", "text/json"],
            "max_size": 50 * 1024 * 1024,  # 50MB
        },
        ".jsonl": {
            "mime_types": ["application/x-ndjson", "text/plain"],
            "max_size": 50 * 1024 * 1024,  # 50MB
        },
        ".xlsx": {
            "mime_types": [
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ],
            "max_size": 50 * 1024 * 1024,  # 50MB
        },
        ".xls": {
            "mime_types": ["application/vnd.ms-excel"],
            "max_size": 50 * 1024 * 1024,  # 50MB
        },
    }

    DANGEROUS_PATTERNS = [
        r"=\s*cmd\s*\|",
        r"=\s*system\s*\(",
        r"@import\s+url\s*\(",
        r"javascript\s*:",
        r"data\s*:\s*text/html",
        r"<script[^>]*>",
        r"vbscript\s*:",
        r"file\s*://",
        r"\\\\[^\\]+\\",
    ]

    def __init__(self) -> None:
        pass

    def validate_upload(
        self, contents: str, filename: str
    ) -> Dict[str, Any]:
        if not contents or not filename:
            return {"valid": False, "error": "Missing file content or filename"}

        basic = self._validate_basic_format(contents, filename)
        if not basic["valid"]:
            return basic

        file_bytes, content_type = self._decode_file_content(contents)
        type_check = self._validate_file_type(filename, content_type, len(file_bytes))
        if not type_check["valid"]:
            return type_check

        security = self._validate_security(file_bytes)
        if not security["valid"]:
            return security

        content_result = self._validate_content_format(file_bytes, filename)
        if not content_result["valid"]:
            return content_result

        return {
            "valid": True,
            "filename": filename,
            "size": len(file_bytes),
            "content_type": content_type,
            "file_extension": Path(filename).suffix.lower(),
            "estimated_rows": content_result.get("estimated_rows", 0),
            "estimated_columns": content_result.get("estimated_columns", 0),
        }

    def _validate_basic_format(self, contents: str, filename: str) -> Dict[str, Any]:
        if not contents.startswith("data:"):
            return {"valid": False, "error": "Invalid file format - must be data URL"}
        if "," not in contents:
            return {"valid": False, "error": "Invalid data URL format"}
        return {"valid": True}

    def _decode_file_content(self, contents: str) -> Tuple[bytes, str]:
        header, data = contents.split(",", 1)
        content_type = "application/octet-stream"
        if ";" in header:
            content_type = header.split(";")[0].replace("data:", "")
        try:
            file_bytes = base64.b64decode(data, validate=True)
        except Exception:
            padding = 4 - (len(data) % 4)
            if padding != 4:
                data += "=" * padding
            file_bytes = base64.b64decode(data, validate=False)
        return file_bytes, content_type

    def _validate_file_type(self, filename: str, content_type: str, size: int) -> Dict[str, Any]:
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.SUPPORTED_TYPES:
            return {
                "valid": False,
                "error": f"Unsupported file type: {file_ext}",
            }
        config = self.SUPPORTED_TYPES[file_ext]
        if size > config["max_size"]:
            max_mb = config["max_size"] / (1024 * 1024)
            return {
                "valid": False,
                "error": f"File too large. Maximum size for {file_ext}: {max_mb:.1f}MB",
            }
        return {"valid": True}

    def _validate_security(self, file_bytes: bytes) -> Dict[str, Any]:
        try:
            text = UnicodeProcessor.safe_encode_text(
                file_bytes.decode("utf-8", "ignore")
            )
        except Exception:
            text = UnicodeProcessor.safe_encode_text(
                file_bytes.decode("utf-8", "ignore")
            )

        for pattern in self.DANGEROUS_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return {
                    "valid": False,
                    "error": "File contains potentially dangerous content",
                }

        if self._calculate_control_char_ratio(text) > 0.1:
            return {"valid": False, "error": "File contains excessive control characters"}

        return {"valid": True}

    def _validate_content_format(self, file_bytes: bytes, filename: str) -> Dict[str, Any]:
        ext = Path(filename).suffix.lower()
        if ext == ".csv":
            return self._validate_csv_content(file_bytes)
        if ext == ".json":
            return self._validate_json_content(file_bytes)
        if ext == ".jsonl":
            return self._validate_jsonl_content(file_bytes)
        if ext in {".xlsx", ".xls"}:
            return self._validate_excel_content(file_bytes)
        return {"valid": False, "error": f"Unsupported file type: {ext}"}

    def _validate_csv_content(self, file_bytes: bytes) -> Dict[str, Any]:
        text = UnicodeProcessor.safe_encode_text(
            file_bytes.decode("utf-8", "ignore")
        )
        lines = text.strip().split("\n")
        if len(lines) < 1:
            return {"valid": False, "error": "CSV file appears to be empty"}
        first = lines[0]
        estimated_columns = len(re.split(r"[,;\t|]", first))
        if estimated_columns < 1:
            return {"valid": False, "error": "CSV file has no detectable columns"}
        return {
            "valid": True,
            "estimated_rows": len(lines) - 1,
            "estimated_columns": estimated_columns,
        }

    def _validate_json_content(self, file_bytes: bytes) -> Dict[str, Any]:
        try:
            text = UnicodeProcessor.safe_encode_text(
                file_bytes.decode("utf-8", "ignore")
            )
            data = json.loads(text)
            if isinstance(data, list):
                rows = len(data)
                cols = len(data[0]) if data and isinstance(data[0], dict) else 0
            elif isinstance(data, dict):
                rows = 1
                cols = len(data)
            else:
                return {"valid": False, "error": "JSON must be an object or array"}
            return {"valid": True, "estimated_rows": rows, "estimated_columns": cols}
        except json.JSONDecodeError as exc:
            return {"valid": False, "error": f"Invalid JSON format: {exc}"}
        except Exception as exc:
            return {"valid": False, "error": f"JSON validation failed: {exc}"}

    def _validate_jsonl_content(self, file_bytes: bytes) -> Dict[str, Any]:
        text = UnicodeProcessor.safe_encode_text(
            file_bytes.decode("utf-8", "ignore")
        )
        lines = text.strip().split("\n")
        valid_lines = 0
        cols = 0
        for line in lines:
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
                valid_lines += 1
                if isinstance(obj, dict):
                    cols = max(cols, len(obj))
            except json.JSONDecodeError:
                continue
        if valid_lines == 0:
            return {"valid": False, "error": "No valid JSON lines found"}
        return {
            "valid": True,
            "estimated_rows": valid_lines,
            "estimated_columns": cols,
        }

    def _validate_excel_content(self, file_bytes: bytes) -> Dict[str, Any]:
        if len(file_bytes) < 8:
            return {"valid": False, "error": "File too small to be valid Excel"}
        try:
            df = pd.read_excel(io.BytesIO(file_bytes), nrows=0)
            cols = len(df.columns)
            df_sample = pd.read_excel(io.BytesIO(file_bytes), nrows=100)
            rows = len(df_sample)
            return {"valid": True, "estimated_rows": rows, "estimated_columns": cols}
        except Exception:
            return {"valid": True, "estimated_rows": 0, "estimated_columns": 0}

    def _calculate_control_char_ratio(self, content: str) -> float:
        control_chars = sum(1 for c in content if ord(c) < 32 and c not in "\t\n\r")
        return control_chars / len(content) if content else 0.0


def validate_dataframe_content(df: pd.DataFrame) -> Dict[str, Any]:
    if df.empty:
        return {"valid": False, "error": "DataFrame is empty", "issues": ["empty_dataframe"]}

    issues = []
    warnings = []

    if len(df.columns) == 0:
        return {"valid": False, "error": "DataFrame has no columns", "issues": ["no_columns"]}

    if len(df.columns) != len(set(df.columns)):
        issues.append("duplicate_columns")
        warnings.append("DataFrame contains duplicate column names")

    empty_columns = df.columns[df.isnull().all()].tolist()
    if empty_columns:
        issues.append("empty_columns")
        warnings.append(f"Columns with no data: {empty_columns}")

    total_cells = len(df) * len(df.columns)
    null_cells = df.isnull().sum().sum()
    empty_string_cells = (df == "").sum().sum()
    null_ratio = null_cells / total_cells if total_cells > 0 else 0
    empty_ratio = (null_cells + empty_string_cells) / total_cells if total_cells > 0 else 0

    if empty_ratio > 0.5:
        issues.append("high_empty_ratio")
        warnings.append(f"High percentage of empty cells: {empty_ratio:.1%}")

    suspicious_cols = [
        col
        for col in df.columns
        if any(prefix in str(col).lower() for prefix in ["=", "+", "-", "@", "cmd", "system"])
    ]
    if suspicious_cols:
        issues.append("suspicious_column_names")
        warnings.append(f"Suspicious column names detected: {suspicious_cols}")

    return {
        "valid": len(issues) == 0 or all(issue in ["empty_columns", "high_empty_ratio"] for issue in issues),
        "rows": len(df),
        "columns": len(df.columns),
        "null_ratio": null_ratio,
        "empty_ratio": empty_ratio,
        "issues": issues,
        "warnings": warnings,
        "column_names": list(df.columns),
        "memory_usage": df.memory_usage(deep=True).sum(),
    }


def validate_uploaded_file(contents: str, filename: str) -> Dict[str, Any]:
    validator = FileContentValidator()
    return validator.validate_upload(contents, filename)


# ---------------------------------------------------------------------------
# Backwards compatibility helpers
# ---------------------------------------------------------------------------

def decode_bytes(data: bytes, enc: str) -> str:
    return data.decode(enc, errors="surrogatepass")


def safe_decode_with_unicode_handling(data: bytes, enc: str) -> str:
    try:
        text = data.decode(enc, errors="surrogatepass")
    except UnicodeDecodeError:
        text = data.decode(enc, errors="replace")

    text = UnicodeProcessor.clean_surrogate_chars(text)

    from security.unicode_security_handler import UnicodeSecurityHandler

    cleaned = UnicodeSecurityHandler.sanitize_unicode_input(text)
    return cleaned.replace("\ufffd", "")


def safe_decode_file(contents: str) -> Optional[bytes]:
    try:
        if "," not in contents:
            return None
        _, content_string = contents.split(",", 1)
        decoded = base64.b64decode(content_string)
        if not decoded:
            return None
        return decoded
    except (base64.binascii.Error, ValueError):
        return None
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error decoding file", exc_info=exc)
        raise


def process_dataframe(decoded: bytes, filename: str) -> Tuple[Optional[pd.DataFrame], Optional[str]]:
    try:
        filename_lower = filename.lower()
        if filename_lower.endswith(".csv"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    df = pd.read_csv(
                        io.StringIO(text),
                        on_bad_lines="skip",
                        encoding="utf-8",
                        low_memory=False,
                        dtype=str,
                        keep_default_na=False,
                    )
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode CSV with any standard encoding"
        elif filename_lower.endswith(".json"):
            for encoding in ["utf-8", "latin-1", "cp1252"]:
                try:
                    text = safe_decode_with_unicode_handling(decoded, encoding)
                    json_data = json.loads(text)
                    if isinstance(json_data, list):
                        cleaned = [
                            {
                                k: UnicodeProcessor.clean_surrogate_chars(v)
                                for k, v in obj.items()
                            }
                            if isinstance(obj, dict)
                            else obj
                            for obj in json_data
                        ]
                        df = pd.DataFrame(cleaned)
                    else:
                        cleaned = (
                            {
                                k: UnicodeProcessor.clean_surrogate_chars(v)
                                for k, v in json_data.items()
                            }
                            if isinstance(json_data, dict)
                            else json_data
                        )
                        df = pd.DataFrame([cleaned])
                    return df, None
                except UnicodeDecodeError:
                    continue
            return None, "Could not decode JSON with any standard encoding"
        elif filename_lower.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(decoded))
            return df, None
        else:
            return None, f"Unsupported file type: {filename}"
    except (
        UnicodeDecodeError,
        ValueError,
        pd.errors.ParserError,
        json.JSONDecodeError,
    ) as e:
        return None, f"Error processing file: {str(e)}"
    except Exception as exc:  # pragma: no cover
        logger.exception("Unexpected error processing file", exc_info=exc)
        raise


__all__ = [
    "FileContentValidator",
    "FileValidationError",
    "SecurityValidationError",
    "validate_dataframe_content",
    "validate_uploaded_file",
    "decode_bytes",
    "safe_decode_with_unicode_handling",
    "safe_decode_file",
    "process_dataframe",
]
