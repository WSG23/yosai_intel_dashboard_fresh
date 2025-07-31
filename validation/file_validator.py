from __future__ import annotations

import base64
import csv
import io
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple

if TYPE_CHECKING:  # pragma: no cover - optional dependency
    from yosai_intel_dashboard.src.services.upload.protocols import UploadValidatorProtocol
else:
    UploadValidatorProtocol = Any

from .core import ValidationResult
from .rules import CompositeValidator, ValidationRule


class FileSizeRule(ValidationRule):
    def __init__(self, max_bytes: int) -> None:
        self.max_bytes = max_bytes

    def validate(self, data: Tuple[str, bytes]) -> ValidationResult:
        filename, content = data
        if len(content) > self.max_bytes:
            return ValidationResult(False, data, ["file_too_large"])
        return ValidationResult(True, data)


class ExtensionRule(ValidationRule):
    def __init__(self, allowed: Iterable[str]) -> None:
        self.allowed = {e.lower() for e in allowed}

    def validate(self, data: Tuple[str, bytes]) -> ValidationResult:
        filename, content = data
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed:
            return ValidationResult(False, data, ["invalid_extension"])
        return ValidationResult(True, data)


class CSVFormulaRule(ValidationRule):
    """Detect potential spreadsheet injection payloads."""

    def validate(self, data: Tuple[str, bytes]) -> ValidationResult:
        filename, content = data
        if Path(filename).suffix.lower() != ".csv":
            return ValidationResult(True, data)
        text = content.decode("utf-8", errors="ignore")
        reader = csv.reader(io.StringIO(text))
        try:
            for row in reader:
                for cell in row:
                    if cell.startswith(("=", "+", "-", "@")):
                        return ValidationResult(False, data, ["formula_injection"])
        except csv.Error:
            return ValidationResult(False, data, ["csv_error"])
        return ValidationResult(True, data)


logger = logging.getLogger(__name__)


class FileValidator(CompositeValidator):
    """High level file validator based on configurable rules."""

    def __init__(
        self,
        max_size_mb: int | None = None,
        allowed_ext: Iterable[str] | None = None,
        validator: UploadValidatorProtocol | None = None,
    ) -> None:
        if max_size_mb is None:
            from config.dynamic_config import dynamic_config

            size_mb = getattr(dynamic_config.security, "max_upload_mb", 10)
        else:
            size_mb = max_size_mb
        size = size_mb * 1024 * 1024
        from config.dynamic_config import dynamic_config

        default_types = getattr(dynamic_config, "upload", None)
        if default_types and hasattr(default_types, "allowed_file_types"):
            defaults = default_types.allowed_file_types
        else:
            defaults = [".csv", ".json", ".xlsx", ".xls"]
        allowed = allowed_ext or defaults
        rules = [
            FileSizeRule(size),
            ExtensionRule(allowed),
            CSVFormulaRule(),
        ]
        super().__init__(rules)
        self.validator = validator

    def _decode_content(self, content: str | bytes) -> bytes:
        if isinstance(content, bytes):
            return content
        try:
            data = content.split(",", 1)[1]
            return base64.b64decode(data)
        except Exception:
            return b""

    def validate_file_upload(self, filename: str, content: bytes) -> dict:
        result = self.validate((filename, content))
        if not result.valid:
            return {"valid": False, "issues": result.issues or []}
        size_mb = len(content) / (1024 * 1024)
        return {"valid": True, "filename": filename, "size_mb": size_mb}

    # ------------------------------------------------------------------
    def validate(self, filename: str, content: str) -> Tuple[bool, str]:
        data = self._decode_content(content)
        res = self.validate_file_upload(filename, data)
        if not res["valid"]:
            return False, ", ".join(res["issues"])
        if self.validator:
            try:
                return self.validator.validate(filename, content)
            except Exception as exc:  # pragma: no cover - delegate errors
                logger.error("Validation failed for %s: %s", filename, exc)
                return False, str(exc)
        return True, ""

    def validate_files(
        self, contents: List[str], filenames: List[str]
    ) -> Dict[str, str]:
        results: Dict[str, str] = {}
        for content, name in zip(contents, filenames):
            ok, msg = self.validate(name, content)
            if not ok:
                results[name] = msg or "invalid"
        return results
