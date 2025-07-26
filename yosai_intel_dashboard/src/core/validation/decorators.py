"""Decorators for validating function inputs and outputs."""

from __future__ import annotations

from functools import wraps
from typing import Any, Callable, Type

from pydantic import BaseModel, ValidationError as PydanticValidationError

from core.exceptions import ValidationError


def validate_input(schema: Type[BaseModel]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Validate the first argument to ``func`` using ``schema``."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(data: Any, *args: Any, **kwargs: Any) -> Any:
            try:
                validated = schema.model_validate(data)
            except PydanticValidationError as exc:  # pragma: no cover - pass through
                raise ValidationError(str(exc))
            return func(validated, *args, **kwargs)

        return wrapper

    return decorator


def validate_output(schema: Type[BaseModel]) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Validate the return value of ``func`` using ``schema``."""

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            try:
                validated = schema.model_validate(result)
            except PydanticValidationError as exc:  # pragma: no cover - pass through
                raise ValidationError(str(exc))
            return validated

        return wrapper

    return decorator


__all__ = ["validate_input", "validate_output"]
