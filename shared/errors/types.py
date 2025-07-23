from enum import Enum


class ErrorCode(str, Enum):
    """Common error codes returned by services."""

    INVALID_INPUT = "invalid_input"
    UNAUTHORIZED = "unauthorized"
    NOT_FOUND = "not_found"
    INTERNAL = "internal"
    UNAVAILABLE = "unavailable"
