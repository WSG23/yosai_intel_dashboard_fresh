"""
File Processing Service for Yōsai Intel Dashboard
"""

import pandas as pd
import io
import json
import logging
from typing import Dict, Any, List
from pathlib import Path

from .base import BaseService
from services.data_processing.core.protocols import FileProcessorProtocol
from utils.file_validator import safe_decode_with_unicode_handling
from core.unicode import (
    sanitize_unicode_input,
    sanitize_data_frame,
    process_large_csv_content,
)
from config.dynamic_config import dynamic_config

logger = logging.getLogger(__name__)


class FileProcessorService(BaseService):
    """File processing service implementation"""

    ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}
    MAX_FILE_SIZE_MB = dynamic_config.get_max_upload_size_mb()

    # Encoding detection order for robust decoding
    ENCODING_PRIORITY = [
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "latin1",
        "cp1252",
        "iso-8859-1",
        "ascii",
    ]

    # Default CSV parsing options
    CSV_OPTIONS: Dict[str, Any] = {
        "low_memory": False,
        "dtype": str,
        "keep_default_na": False,
        "na_filter": False,
        "skipinitialspace": True,
    }

    def __init__(self):
        super().__init__("file_processor")

    def _do_initialize(self) -> None:
        """Initialize file processor"""
        pass  # No special initialization needed

    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded file"""
        filename = sanitize_unicode_input(filename)
        issues = []

        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            issues.append(
                f"File type {file_ext} not allowed. Allowed: {self.ALLOWED_EXTENSIONS}"
            )

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.MAX_FILE_SIZE_MB:
            issues.append(
                f"File too large: {size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB"
            )

        # Check for empty file
        if len(content) == 0:
            issues.append("File is empty")

        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "size_mb": size_mb,
            "extension": file_ext,
        }

    def process_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Process uploaded file and return DataFrame"""
        try:
            filename = sanitize_unicode_input(filename)
            file_ext = Path(filename).suffix.lower()

            if file_ext == ".csv":
                return self._process_csv(file_content)
            elif file_ext == ".json":
                return self._process_json(file_content)
            elif file_ext in [".xlsx", ".xls"]:
                return self._process_excel(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_ext}")

        except Exception as e:
            logger.error(f"Error processing file {filename}: {e}")
            raise

    def _process_csv(self, content: bytes) -> pd.DataFrame:
        """Process CSV file with robust Unicode handling."""
        logger.debug("Processing CSV content")

        if len(content) > 10 * 1024 * 1024:
            text_content = process_large_csv_content(content)
        else:
            text_content = self._decode_with_fallback(content)

        delimiters = [",", ";", "\t", "|"]

        for delim in delimiters:
            try:
                df = pd.read_csv(io.StringIO(text_content), sep=delim, **self.CSV_OPTIONS)
                if len(df.columns) > 1 or (len(df.columns) == 1 and len(df) > 0):
                    logger.debug("Successfully parsed CSV with delimiter '%s'", delim)
                    return sanitize_data_frame(df)
            except Exception as exc:
                logger.debug("Failed to parse with delimiter '%s': %s", delim, exc)
                continue

        try:
            df = pd.read_csv(
                io.StringIO(text_content),
                engine="python",
                sep=None,
                **self.CSV_OPTIONS,
            )
            return sanitize_data_frame(df)
        except Exception as exc:
            raise ValueError(f"Could not parse CSV file: {exc}")

    def _process_json(self, content: bytes) -> pd.DataFrame:
        """Process JSON file with robust decoding."""
        logger.debug("Processing JSON content")
        text_content = self._decode_with_fallback(content)

        try:
            data = json.loads(text_content)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("JSON must be an object or array")
            return sanitize_data_frame(df)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON format: {exc}")
        except Exception as e:
            raise ValueError(f"Error reading JSON: {e}")

    def _process_excel(self, content: bytes) -> pd.DataFrame:
        """Process Excel file"""
        logger.debug("Processing Excel content")
        try:
            df = pd.read_excel(io.BytesIO(content), dtype=str, keep_default_na=False)
            return sanitize_data_frame(df)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")

    def _decode_with_fallback(self, content: bytes) -> str:
        """Decode bytes using multiple encodings with basic heuristics."""
        for enc in self.ENCODING_PRIORITY:
            try:
                text = safe_decode_with_unicode_handling(content, enc)
                if self._is_reasonable_text(text):
                    logger.debug("Decoded content using %s", enc)
                    return text
            except Exception:
                continue
        logger.warning("All encodings failed, using replacement characters")
        return content.decode("utf-8", errors="replace")

    def _is_reasonable_text(self, text: str) -> bool:
        """Basic check to ensure decoded text looks valid."""
        if not text.strip():
            return False

        replacement_ratio = text.count("\ufffd") / len(text)
        if replacement_ratio > 0.1:
            return False

        printable = sum(1 for c in text if c.isprintable() or c.isspace())
        return (printable / len(text)) > 0.7

