"""Flask request validation middleware."""

from flask import request, Response
from typing import Callable

from .validation_exceptions import ValidationError
from .input_validator import InputValidator, Validator

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

    def __init__(self) -> None:
        self.orchestrator = ValidationOrchestrator([InputValidator()])

    def validate_request(self) -> None:
        if request.data:
            try:
                request._cached_data = self.orchestrator.validate(request.data.decode("utf-8", errors="ignore")).encode("utf-8")
            except ValidationError:
                return Response("Bad Request", status=400)
        return None

    def sanitize_response(self, response: Response) -> Response:
        return response
