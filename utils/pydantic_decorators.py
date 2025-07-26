from __future__ import annotations

from functools import wraps
from typing import Any, Type

from flask import abort, jsonify, request
from pydantic import BaseModel, ValidationError


def validate_input(model: Type[BaseModel]):
    """Validate request JSON against ``model`` and pass instance as ``payload``."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            data = request.get_json(silent=True) or {}
            try:
                validated = model.model_validate(data)
            except ValidationError as exc:  # pragma: no cover - runtime check
                abort(400, description=str(exc))
            kwargs["payload"] = validated
            return func(*args, **kwargs)

        return wrapper

    return decorator


def validate_output(model: Type[BaseModel]):
    """Validate and jsonify endpoint output using ``model``."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
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
                abort(500, description=str(exc))
            return jsonify(body_data), status

        return wrapper

    return decorator
