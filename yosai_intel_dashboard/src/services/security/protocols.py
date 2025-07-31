"""Security service protocols."""

from __future__ import annotations

from abc import abstractmethod
from typing import Any, Protocol


class SecurityServiceProtocol(Protocol):
    """Perform security checks."""

    @abstractmethod
    def validate(self, data: Any) -> bool: ...


class AuthenticationProtocol(Protocol):
    """Authentication provider."""

    @abstractmethod
    def authenticate(self, token: str) -> bool: ...
