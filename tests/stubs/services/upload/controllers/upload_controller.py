from typing import Any

from validation.security_validator import SecurityValidator


class UnifiedUploadController:
    def __init__(self, validator: SecurityValidator | None = None) -> None:
        self._validator = validator or SecurityValidator()

    def parse_upload(self, contents: str, filename: str, user: Any | None = None):
        if user is not None:
            self._validator.validate_resource_id(user, filename)
        return None
