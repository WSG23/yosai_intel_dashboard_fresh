"""Security Domain Public API."""

import secrets
import time
from functools import wraps
from typing import Callable

from flask import jsonify, request

from yosai_intel_dashboard.src.infrastructure.security.unicode_security_validator import (  # noqa: E501
    UnicodeSecurityValidator as SecurityValidator,
)

from .behavioral_biometrics import verify_behavioral_biometrics
from .jwt_service import (
    TokenValidationError,
    generate_refresh_jwt,
    generate_service_jwt,
    generate_token_pair,
    invalidate_jwt_secret_cache,
    refresh_access_token,
    verify_refresh_jwt,
    verify_service_jwt,
)
from .rbac_adapter import has_permission as _rbac_has_permission
from .protocols import AuthenticationProtocol, SecurityServiceProtocol


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


def require_permission(permission: str) -> Callable:
    """Flask decorator enforcing RBAC using JWT roles."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            auth = request.headers.get("Authorization", "")
            if not auth.startswith("Bearer "):
                return jsonify({"error": "unauthorized"}), 401
            token = auth.split(" ", 1)[1]
            try:
                claims = verify_service_jwt(token)
            except TokenValidationError:
                return jsonify({"error": "unauthorized"}), 401
            role = claims.get("role")
            if role is None or not _rbac_has_permission(role, permission):
                return jsonify({"error": "forbidden"}), 403
            if not verify_behavioral_biometrics(request):
                return jsonify({"error": "biometric-anomaly"}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator


def require_role(role: str) -> Callable:
    """Flask decorator enforcing a role header."""

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            roles = [
                r.strip()
                for r in request.headers.get("X-Roles", "").split(",")
                if r.strip()
            ]
            if role not in roles:
                return jsonify({"error": "forbidden"}), 403
            if not verify_behavioral_biometrics(request):
                return jsonify({"error": "biometric-anomaly"}), 403
            return func(*args, **kwargs)

        return wrapper

    return decorator


__all__ = [
    "SecurityServiceProtocol",
    "AuthenticationProtocol",
    "SecurityValidator",
    "ServiceTokenManager",
    "AuthenticationService",
    "generate_service_token",
    "rotate_service_token",
    "generate_service_jwt",
    "generate_refresh_jwt",
    "generate_token_pair",
    "verify_service_jwt",
    "verify_refresh_jwt",
    "refresh_access_token",
    "invalidate_jwt_secret_cache",
    "require_token",
    "require_permission",
    "require_role",
]
