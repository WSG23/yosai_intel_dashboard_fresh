"""Data models for user command and query operations."""

from __future__ import annotations

from pydantic import BaseModel


class UserCommand(BaseModel):
    """Model representing a write operation on a user.

    Attributes:
        user_id: Unique identifier of the user to create or modify.
        name: Human readable name associated with the user.
    """

    user_id: str
    name: str


class UserQuery(BaseModel):
    """Model representing a read operation for a user."""

    user_id: str


__all__ = ["UserCommand", "UserQuery"]
