"""Unified error handling utilities."""

from .api_error_response import api_error_response, fastapi_error_response, serialize_error
from .api_errors import http_error
from .core import ErrorContext, ErrorHandler
from .decorators import handle_errors
from .exceptions import ErrorCategory, YosaiException
from .flask import register_error_handlers
from .middleware import ErrorHandlingMiddleware

__all__ = [
    "ErrorHandler",
    "ErrorContext",
    "handle_errors",
    "YosaiException",
    "ErrorCategory",
    "api_error_response",
    "fastapi_error_response",
    "serialize_error",
    "http_error",
    "ErrorHandlingMiddleware",
    "register_error_handlers",
]
