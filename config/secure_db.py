"""Helpers for executing sanitized database queries."""
from __future__ import annotations

from database.secure_exec import execute_secure_query

__all__ = ["execute_secure_query"]
