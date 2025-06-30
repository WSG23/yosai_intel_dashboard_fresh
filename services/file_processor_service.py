"""Compatibility wrapper around :class:`FileProcessor`.

This module exists for backward compatibility. It exposes
``FileProcessorService`` which delegates all logic to
:class:`~services.file_processor.FileProcessor`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any

from .file_processor import FileProcessor

logger = logging.getLogger(__name__)


class FileProcessorService(FileProcessor):
    """Thin wrapper for the :class:`FileProcessor` class."""

    ALLOWED_EXTENSIONS = {".csv", ".json", ".xlsx", ".xls"}
    MAX_FILE_SIZE_MB = 100

    def __init__(self, upload_folder: str = "temp", allowed_extensions: set | None = None) -> None:
        exts = allowed_extensions or {ext.lstrip(".") for ext in self.ALLOWED_EXTENSIONS}
        super().__init__(upload_folder=upload_folder, allowed_extensions=exts)

    def validate_file(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate an uploaded file.

        Parameters
        ----------
        filename:
            Name of the uploaded file.
        content:
            Raw file bytes.
        """
        file_ext = Path(filename).suffix.lower()
        size_mb = len(content) / (1024 * 1024)
        issues = []

        if file_ext not in self.ALLOWED_EXTENSIONS:
            issues.append(
                f"File type {file_ext} not allowed. Allowed: {self.ALLOWED_EXTENSIONS}"
            )
        if size_mb > self.MAX_FILE_SIZE_MB:
            issues.append(f"File too large: {size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB")
        if not content:
            issues.append("File is empty")

        return {
            "valid": not issues,
            "issues": issues,
            "size_mb": size_mb,
            "extension": file_ext,
        }
