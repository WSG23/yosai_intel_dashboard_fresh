from __future__ import annotations

from functools import wraps
from typing import Any, Type, Callable, TypeVar

from flask import jsonify, request
from pydantic import BaseModel, ValidationError

from error_handling import ErrorCategory, ErrorHandler
from shared.errors.types import ErrorCode
from yosai_framework.errors import CODE_TO_STATUS

handler = ErrorHandler()

F = TypeVar("F", bound=Callable[..., Any])


def validate_input(model: Type[BaseModel]) -> Callable[[F], F]:
    """Validate request JSON against ``model`` and pass instance as ``payload``."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            data = request.get_json(silent=True) or {}
            try:
                validated = model.model_validate(data)
            except ValidationError as exc:  # pragma: no cover - runtime check
                err = handler.handle(exc, ErrorCategory.INVALID_INPUT)
                return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INVALID_INPUT]
            kwargs["payload"] = validated
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_output(model: Type[BaseModel]) -> Callable[[F], F]:
    """Validate and jsonify endpoint output using ``model``."""

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            if isinstance(result, tuple):
                body, status = result[0], result[1]
            else:
                body, status = result, 200

            if hasattr(body, "get_json"):
                body_data = body.get_json()
            else:
                body_data = body
            try:
                model.model_validate(body_data)
            except ValidationError as exc:  # pragma: no cover - runtime check
                err = handler.handle(exc, ErrorCategory.INTERNAL)
                return jsonify(err.to_dict()), CODE_TO_STATUS[ErrorCode.INTERNAL]
            return jsonify(body_data), status

        return wrapper

    return decorator
