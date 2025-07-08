"""Security domain protocols."""
from abc import abstractmethod
from typing import Any, Dict, List, Protocol, runtime_checkable


@runtime_checkable
class AuthenticationProtocol(Protocol):
    """Protocol for authentication operations."""

    @abstractmethod
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate user credentials."""
        ...

    @abstractmethod
    def validate_token(self, token: str) -> Dict[str, Any]:
        """Validate authentication token."""
        ...


@runtime_checkable
class AuthorizationProtocol(Protocol):
    """Protocol for authorization operations."""

    @abstractmethod
    def check_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Check if user has permission for action on resource."""
        ...

    @abstractmethod
    def get_user_roles(self, user_id: str) -> List[str]:
        """Get roles assigned to user."""
        ...
