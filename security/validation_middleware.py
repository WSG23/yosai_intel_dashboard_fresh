"""Flask request validation middleware."""

from typing import Callable, Optional, Protocol

from flask import Response, request

from analytics_core.callbacks.unified_callback_manager import CallbackManager
from validation.security_validator import SecurityValidator
from yosai_intel_dashboard.src.core.callback_events import CallbackEvent
from core.exceptions import ValidationError
from config.dynamic_config import (
    dynamic_config,
)


class Validator(Protocol):
    def validate(self, data: str) -> str: ...


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
        class _Adapter:
            def __init__(self) -> None:
                self.validator = SecurityValidator()

            def validate(self, data: str) -> str:
                result = self.validator.validate_input(data, "request")
                if not result["valid"]:
                    raise ValidationError("Invalid input")
                return result["sanitized"]

        self.orchestrator = ValidationOrchestrator([_Adapter()])
        self.max_body_size = dynamic_config.security.max_upload_mb * 1024 * 1024

    def handle_registers(self, manager: CallbackManager) -> None:
        """Register validation hooks with the callback manager."""
        manager.handle_register(CallbackEvent.BEFORE_REQUEST, self.validate_request)
        manager.handle_register(CallbackEvent.AFTER_REQUEST, self.sanitize_response)

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
                from yosai_intel_dashboard.src.core.unicode import (
                    safe_unicode_decode,
                    sanitize_for_utf8,
                )

                raw_text = safe_unicode_decode(request.data, "utf-8")
                sanitized = sanitize_for_utf8(raw_text)
                request._cached_data = self.orchestrator.validate(sanitized).encode(
                    "utf-8"
                )
            except ValidationError:
                return Response("Bad Request", status=400)
        return None

    def sanitize_response(self, response: Response) -> Response:
        return response
