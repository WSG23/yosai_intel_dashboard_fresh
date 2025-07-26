"""Pydantic models for request and response validation."""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field


class UserCreateSchema(BaseModel):
    """Schema for creating a new user."""

    username: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8)


class UserResponseSchema(BaseModel):
    """Schema returned for user information."""

    id: int
    username: str
    email: EmailStr


__all__ = [
    "UserCreateSchema",
    "UserResponseSchema",
]
