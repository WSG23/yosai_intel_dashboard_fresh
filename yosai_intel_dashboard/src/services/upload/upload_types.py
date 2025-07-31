from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class ValidationResult:
    """Result of validating an uploaded file."""

    valid: bool
    message: str = ""


@dataclass
class UploadResult:
    """Simplified container for upload results."""

    alerts: List[Any]
    previews: List[Any]
    info: Dict[str, Any]
    navigation: List[Any]
    current_file: Dict[str, Any]
