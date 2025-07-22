"""Security Domain Public API."""

from .protocols import SecurityServiceProtocol, AuthenticationProtocol
from security.unicode_security_validator import (
    UnicodeSecurityValidator as SecurityValidator,
)

import secrets
import time
from functools import wraps
from typing import Callable

from flask import jsonify, request


class ServiceTokenManager:
    """Generate and rotate simple service tokens."""

    def __init__(self, rotation_seconds: int = 3600) -> None:
        self.rotation_seconds = rotation_seconds
        self._token = self._generate()
        self._expires_at = time.time() + self.rotation_seconds

    def _generate(self) -> str:
        return secrets.token_urlsafe(32)

    def get_token(self) -> str:
        if time.time() >= self._expires_at:
            self.rotate()
        return self._token

    def rotate(self) -> str:
        self._token = self._generate()
        self._expires_at = time.time() + self.rotation_seconds
        return self._token

    def validate(self, token: str) -> bool:
        return token == self._token


_token_manager = ServiceTokenManager()


class AuthenticationService:
    """Simple authentication service using :class:`ServiceTokenManager`."""

    def __init__(self, manager: ServiceTokenManager | None = None) -> None:
        self.manager = manager or _token_manager

    def authenticate(self, token: str) -> bool:
        return self.manager.validate(token)


def generate_service_token() -> str:
    """Return the current service token."""
    return _token_manager.get_token()


def rotate_service_token() -> str:
    """Rotate and return a new service token."""
    return _token_manager.rotate()


def require_token(func: Callable) -> Callable:
    """Flask decorator enforcing token-based auth."""

    @wraps(func)
    def wrapper(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"error": "unauthorized"}), 401
        token = auth.split(" ", 1)[1]
        if not _token_manager.validate(token):
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)

    return wrapper


__all__ = [
    "SecurityServiceProtocol",
    "AuthenticationProtocol",
    "SecurityValidator",
    "ServiceTokenManager",
    "AuthenticationService",
    "generate_service_token",
    "rotate_service_token",
    "require_token",
]
