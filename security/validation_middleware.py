"""Flask request validation middleware."""

from flask import request, Response
from typing import Callable, Optional

from core.callback_events import CallbackEvent
from core.callback_manager import CallbackManager

from config.dynamic_config import dynamic_config

from core.exceptions import ValidationError
from core.security import InputValidator
from typing import Protocol


class Validator(Protocol):
    def validate(self, data: str) -> str:
        ...


class ValidationOrchestrator:
    """Coordinate multiple validators."""

    def __init__(self, validators: list[Validator] | None = None) -> None:
        self.validators = validators or []

    def validate(self, data: str) -> str:
        for v in self.validators:
            data = v.validate(data)
        return data


class ValidationMiddleware:
    """Middleware applying input validation."""

    SAFE_VALIDATION_THRESHOLD = 1 * 1024 * 1024  # 1 MB

    def __init__(self) -> None:
        self.orchestrator = ValidationOrchestrator([InputValidator()])
        self.max_body_size = dynamic_config.security.max_upload_mb * 1024 * 1024

    def register_callbacks(self, manager: CallbackManager) -> None:
        """Register validation hooks with the callback manager."""
        manager.register_callback(CallbackEvent.BEFORE_REQUEST, self.validate_request)
        manager.register_callback(CallbackEvent.AFTER_REQUEST, self.sanitize_response)

    def validate_request(self) -> None:
        # Enforce maximum request body size
        if request.content_length and request.content_length > self.max_body_size:
            return Response("Request Entity Too Large", status=413)

        # Validate query string parameters
        for value in request.args.values():
            try:
                self.orchestrator.validate(value)
            except ValidationError:
                return Response("Bad Request", status=400)

        # Validate body content
        if request.data:
            if request.path.startswith("/_dash-update-component") or (
                request.content_length
                and request.content_length > self.SAFE_VALIDATION_THRESHOLD
            ):
                return None
            try:
                from security.unicode_security_handler import UnicodeSecurityHandler

                raw_text = request.data.decode("utf-8", errors="ignore")
                sanitized = UnicodeSecurityHandler.sanitize_unicode_input(raw_text)
                request._cached_data = self.orchestrator.validate(sanitized).encode(
                    "utf-8"
                )
            except ValidationError:
                return Response("Bad Request", status=400)
        return None

    def sanitize_response(self, response: Response) -> Response:
        return response
