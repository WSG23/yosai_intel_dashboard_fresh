"""Service for handling user write operations."""

from __future__ import annotations

from typing import Dict

from .models import UserCommand


class UserCommandService:
    """Service dedicated to command operations on users."""

    def __init__(self, store: Dict[str, str] | None = None) -> None:
        """Initialize the service with an optional ``store``.

        Args:
            store: Mutable mapping used to persist user data. If ``None`` a new
                dictionary is created.
        """

        self.store: Dict[str, str] = store if store is not None else {}

    def create_user(self, command: UserCommand) -> None:
        """Create or update a user using ``command``."""

        self.store[command.user_id] = command.name


__all__ = ["UserCommandService"]
