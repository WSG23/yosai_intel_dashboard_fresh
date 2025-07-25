import logging
from typing import Dict, List, Tuple

from services.upload.protocols import UploadValidatorProtocol

logger = logging.getLogger(__name__)


class FileValidator:
    """Validate uploaded files using an optional validator."""

    def __init__(self, validator: UploadValidatorProtocol | None = None) -> None:
        self.validator = validator

    def validate(self, filename: str, content: str) -> Tuple[bool, str]:
        """Validate a single file."""
        if not self.validator:
            return True, ""
        try:
            return self.validator.validate(filename, content)
        except Exception as exc:
            logger.error("Validation failed for %s: %s", filename, exc)
            return False, str(exc)

    def validate_files(
        self, contents: List[str], filenames: List[str]
    ) -> Dict[str, str]:
        """Validate multiple files and return error messages by filename."""
        results: Dict[str, str] = {}
        for content, name in zip(contents, filenames):
            ok, msg = self.validate(name, content)
            if not ok:
                results[name] = msg or "invalid"
        return results
