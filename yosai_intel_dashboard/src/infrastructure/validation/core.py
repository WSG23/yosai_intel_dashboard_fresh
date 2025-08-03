from dataclasses import dataclass
from typing import Any, Protocol


@dataclass
class ValidationResult:
    """Outcome of a validation step."""

    valid: bool
    sanitized: Any | None = None
    issues: list[str] | None = None
    remediation: list[str] | None = None


class Validator(Protocol):
    """Basic validator interface."""

    def validate(self, data: Any) -> ValidationResult: ...
