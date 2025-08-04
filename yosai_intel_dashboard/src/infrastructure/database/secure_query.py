"""Compatibility wrapper for SecureQueryBuilder.

The SecureQueryBuilder implementation has moved to
``infrastructure.security.query_builder``. Importing from this module is
deprecated and will be removed in a future release.
"""

from __future__ import annotations

from infrastructure.security.query_builder import (
    SecureQueryBuilder,
    log_sanitized_query,
)

__all__ = ["SecureQueryBuilder", "log_sanitized_query"]
