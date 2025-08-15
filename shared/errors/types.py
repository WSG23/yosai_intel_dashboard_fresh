"""Shared error contract used across services."""

from enum import Enum
from http import HTTPStatus
from typing import Any, Dict

from pydantic import BaseModel


class ErrorCode(str, Enum):
    """Common error codes returned by services."""

    INVALID_INPUT = "invalid_input"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    INTERNAL = "internal"
    UNAVAILABLE = "unavailable"


class ErrorResponse(BaseModel):
    """Standard error response model."""

    code: ErrorCode
    message: str
    details: Any | None = None


# Mapping of :class:`ErrorCode` values to HTTP status codes.
CODE_TO_STATUS: Dict[ErrorCode, int] = {
    ErrorCode.INVALID_INPUT: HTTPStatus.BAD_REQUEST,
    ErrorCode.UNAUTHORIZED: HTTPStatus.UNAUTHORIZED,
    ErrorCode.NOT_FOUND: HTTPStatus.NOT_FOUND,
    ErrorCode.INTERNAL: HTTPStatus.INTERNAL_SERVER_ERROR,
    ErrorCode.UNAVAILABLE: HTTPStatus.SERVICE_UNAVAILABLE,
}


__all__ = ["ErrorCode", "ErrorResponse", "CODE_TO_STATUS"]
