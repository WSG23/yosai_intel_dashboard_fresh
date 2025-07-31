from fastapi import HTTPException

from shared.errors.types import ErrorCode


def http_error(code: ErrorCode, message: str, status: int) -> HTTPException:
    """Return an ``HTTPException`` with a standardized error body."""
    return HTTPException(
        status_code=status,
        detail={"code": code.value, "message": message},
    )


__all__ = ["http_error"]
