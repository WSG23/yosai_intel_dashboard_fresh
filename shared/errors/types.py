from enum import Enum

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

    code: ErrorCode | None = None
    detail: str
