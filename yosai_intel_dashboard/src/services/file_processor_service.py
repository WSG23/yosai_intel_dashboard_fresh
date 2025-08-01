"""
File Processing Service for Yōsai Intel Dashboard
"""

from __future__ import annotations

import csv
import io
import json
import logging
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE, UPLOAD_ALLOWED_EXTENSIONS
from yosai_intel_dashboard.src.core.interfaces.protocols import ConfigurationServiceProtocol
from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor as UnicodeHelper
from yosai_intel_dashboard.src.core.unicode import process_large_csv_content
from yosai_intel_dashboard.src.services.data_processing.base_file_processor import BaseFileProcessor
from yosai_intel_dashboard.src.utils.file_utils import safe_decode_with_unicode_handling
from yosai_intel_dashboard.src.utils.memory_utils import memory_safe
from yosai_intel_dashboard.src.utils.protocols import SafeDecoderProtocol
from validation.file_validator import FileValidator
from yosai_framework.service import BaseService

from .stream_processor import StreamProcessor

logger = logging.getLogger(__name__)


class FileProcessorService(BaseService, BaseFileProcessor):
    """File processing service implementation"""

    ALLOWED_EXTENSIONS = UPLOAD_ALLOWED_EXTENSIONS

    # Default CSV parsing options
    CSV_OPTIONS: Dict[str, Any] = {
        "low_memory": False,
        "dtype": str,
        "keep_default_na": False,
        "na_filter": False,
        "skipinitialspace": True,
    }

    def __init__(
        self,
        config: ConfigurationServiceProtocol,
        decoder: SafeDecoderProtocol = safe_decode_with_unicode_handling,
        validator: FileValidator | None = None,
        *,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
    ) -> None:
        BaseService.__init__(self, "file-processor", "")
        BaseFileProcessor.__init__(self, chunk_size=chunk_size, decoder=decoder)
        self.start()
        self.config = config
        self.max_file_size_mb = config.get_max_upload_size_mb()
        self._validator = validator or FileValidator(
            max_size_mb=self.max_file_size_mb,
            allowed_ext=self.ALLOWED_EXTENSIONS,
        )

    def _do_initialize(self) -> None:
        """Initialize file processor"""
        pass  # No special initialization needed

    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded file using :class:`FileValidator`."""
        filename = UnicodeHelper.clean_text(filename)
        return self._validator.validate_file_upload(filename, content)

    @memory_safe(max_memory_mb=500)
    def process_file(self, file_content: bytes, filename: str) -> pd.DataFrame:
        """Process uploaded file and return DataFrame"""
        try:
            filename = UnicodeHelper.clean_text(filename)
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
            text_content = self.decode_with_fallback(content)

        # Sanitize any surrogate characters that may remain after decoding
        text_content = self.decode_with_surrogate_handling(
            text_content.encode("utf-8", "surrogatepass"),
            "utf-8",
        )

        sample = "\n".join(text_content.splitlines()[:20])
        delimiter = ","
        try:
            dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
            delimiter = dialect.delimiter
        except Exception:
            logger.debug("CSV sniffer failed, falling back to manual detection")

        try:
            df, errors = StreamProcessor.process_large_csv(
                io.StringIO(text_content), sep=delimiter, **self.CSV_OPTIONS
            )

            if errors:
                for msg in errors:
                    logger.error(msg)

            if len(df.columns) <= 1:
                df_alt, alt_err = StreamProcessor.process_large_csv(
                    io.StringIO(text_content),
                    engine="python",
                    sep=None,
                    **self.CSV_OPTIONS,
                )
                errors.extend(alt_err)
                if len(df_alt.columns) > len(df.columns):
                    df = df_alt
            return UnicodeHelper.sanitize_dataframe(df)
        except Exception as exc:
            raise ValueError(f"Could not parse CSV file: {exc}")

    def _process_json(self, content: bytes) -> pd.DataFrame:
        """Process JSON file with robust decoding."""
        logger.debug("Processing JSON content")
        text_content = self.decode_with_fallback(content)

        try:
            data = json.loads(text_content)
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                df = pd.DataFrame([data])
            else:
                raise ValueError("JSON must be an object or array")
            return UnicodeHelper.sanitize_dataframe(df)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON format: {exc}")
        except Exception as e:
            raise ValueError(f"Error reading JSON: {e}")

    def _process_excel(self, content: bytes) -> pd.DataFrame:
        """Process Excel file"""
        logger.debug("Processing Excel content")
        try:
            df = pd.read_excel(io.BytesIO(content), dtype=str, keep_default_na=False)
            return UnicodeHelper.sanitize_dataframe(df)
        except Exception as e:
            raise ValueError(f"Error reading Excel file: {e}")
