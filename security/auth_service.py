"""Minimal security service used for dependency injection."""

from typing import Any, Dict


class SecurityService:
    """Basic placeholder security service."""

    def __init__(self, config: Any) -> None:
        self.config = config

    def enable_input_validation(self) -> None:
        pass

    def enable_rate_limiting(self) -> None:
        pass

    def enable_file_validation(self) -> None:
        pass

    def validate_file(self, filename: str, size: int) -> Dict[str, Any]:
        return {"valid": True}

    def log_file_processing_event(self, filename: str, success: bool, error: str | None = None) -> None:
        pass

    def get_security_status(self) -> Dict[str, Any]:
        return {"overall": "basic"}


__all__ = ["SecurityService"]

