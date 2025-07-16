"""Security Domain Public API."""

from .protocols import SecurityServiceProtocol, AuthenticationProtocol
from security.unicode_security_validator import (
    UnicodeSecurityValidator as SecurityValidator,
)


class AuthenticationService:
    """Placeholder authentication service."""

    def authenticate(self, token: str) -> bool:  # pragma: no cover - simple stub
        return bool(token)


__all__ = [
    "SecurityServiceProtocol",
    "AuthenticationProtocol",
    "SecurityValidator",
    "AuthenticationService",
]
