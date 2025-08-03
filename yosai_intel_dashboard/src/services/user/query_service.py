"""Service for handling user read operations."""

from __future__ import annotations

from typing import Dict, Optional

from .models import UserQuery


class UserQueryService:
    """Service dedicated to querying user information."""

    def __init__(self, store: Dict[str, str] | None = None) -> None:
        """Initialize the service with an optional ``store``.

        Args:
            store: Mutable mapping used to retrieve user data. If ``None`` a new
                dictionary is created.
        """

        self.store: Dict[str, str] = store if store is not None else {}

    def get_user(self, query: UserQuery) -> Optional[str]:
        """Return the user name for ``query.user_id`` if present."""

        return self.store.get(query.user_id)


__all__ = ["UserQueryService"]
