"""
File Processing Service for Yōsai Intel Dashboard
"""

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import chardet
import pandas as pd

from services.configuration_service import ConfigurationServiceProtocol
from core.performance_file_processor import PerformanceFileProcessor
from core.unicode import process_large_csv_content, sanitize_data_frame
from core.unicode_utils import sanitize_for_utf8
from services.data_processing.core.protocols import FileProcessorProtocol
from utils.file_validator import safe_decode_with_unicode_handling

from .base import BaseService

logger = logging.getLogger(__name__)


class FileProcessorService(BaseService):
    """File processing service implementation"""

    ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}

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

    def __init__(self, config: ConfigurationServiceProtocol) -> None:
        super().__init__("file_processor")
        self.config = config
        self.max_file_size_mb = config.get_max_upload_size_mb()

    def _do_initialize(self) -> None:
        """Initialize file processor"""
        pass  # No special initialization needed

    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded file"""
        filename = sanitize_for_utf8(filename)
        issues = []

        # Check file extension
        file_ext = Path(filename).suffix.lower()
        if file_ext not in self.ALLOWED_EXTENSIONS:
            issues.append(
                f"File type {file_ext} not allowed. Allowed: {self.ALLOWED_EXTENSIONS}"
            )

        # Check file size
        size_mb = len(content) / (1024 * 1024)
        if size_mb > self.max_file_size_mb:
            issues.append(
                f"File too large: {size_mb:.1f}MB > {self.max_file_size_mb}MB"
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
            filename = sanitize_for_utf8(filename)
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

        # Sanitize any surrogate characters that may remain after decoding
        text_content = self._decode_with_surrogate_handling(
            text_content.encode("utf-8", "surrogatepass"),
            "utf-8",
        )

        sample = "\n".join(text_content.splitlines()[:20])
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=[",", ";", "\t", "|"])
            delimiter = dialect.delimiter
        except Exception:
            logger.debug("CSV sniffer failed, falling back to manual detection")

        try:
            if len(content) > 10 * 1024 * 1024:
                processor = PerformanceFileProcessor(chunk_size=100000)
                df = processor.process_large_csv(
                    io.StringIO(text_content),
                    max_memory_mb=500,
                )
            else:
                df = pd.read_csv(io.StringIO(text_content), sep=delimiter, **self.CSV_OPTIONS)
            if len(df.columns) <= 1:
                df_alt = pd.read_csv(
                    io.StringIO(text_content),
                    engine="python",
                    sep=None,
                    **self.CSV_OPTIONS,
                )
                if len(df_alt.columns) > len(df.columns):
                    df = df_alt
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
        detected = chardet.detect(content)
        encoding = detected.get("encoding")
        if encoding:
            try:
                text = safe_decode_with_unicode_handling(content, encoding)
                if self._is_reasonable_text(text):
                    logger.debug("Decoded content using detected %s", encoding)
                    return text
            except Exception:
                pass

        for enc in self.ENCODING_PRIORITY:
            try:
                text = safe_decode_with_unicode_handling(content, enc)
                if self._is_reasonable_text(text):
                    logger.debug("Decoded content using %s", enc)
                    return text
            except Exception:
                continue
        from core.unicode_decode import safe_unicode_decode

        logger.warning("All encodings failed, using replacement characters")
        return safe_unicode_decode(content, "utf-8")

    def _decode_with_surrogate_handling(self, data: bytes, encoding: str) -> str:
        """Decode ``data`` and remove surrogate code points."""
        try:
            text = data.decode(encoding, errors="surrogatepass")
        except Exception:
            text = data.decode(encoding, errors="replace")
        return sanitize_for_utf8(text)

    def _is_reasonable_text(self, text: str) -> bool:
        """Basic check to ensure decoded text looks valid."""
        if not text.strip():
            return False

        replacement_ratio = text.count("\ufffd") / len(text)
        if replacement_ratio > 0.1:
            return False

        printable = sum(1 for c in text if c.isprintable() or c.isspace())
        return (printable / len(text)) > 0.7

