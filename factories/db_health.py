"""Pydantic models used by factory helpers."""

from __future__ import annotations

from pydantic import BaseModel


class DBHealthStatus(BaseModel):
    """Schema representing database health information."""

    healthy: bool
    details: dict


__all__ = ["DBHealthStatus"]

