from __future__ import annotations

"""Environment variable validation utilities."""

import os
from typing import Iterable


def validate_env(required_keys: Iterable[str]) -> None:
    """Ensure that all ``required_keys`` are present in the environment.

    Parameters
    ----------
    required_keys:
        Iterable of environment variable names that must be set.

    Raises
    ------
    RuntimeError
        If any required variable is missing or empty.
    """

    missing = [key for key in required_keys if not os.getenv(key)]
    if missing:
        raise RuntimeError(
            "Missing required environment variables: " + ", ".join(missing)
        )


# Environment variables required for application startup
REQUIRED_ENV_VARS: list[str] = [
    "SECRET_KEY",
    "DB_PASSWORD",
    "AUTH0_CLIENT_ID",
    "AUTH0_CLIENT_SECRET",
    "AUTH0_DOMAIN",
    "AUTH0_AUDIENCE",
    "JWT_SECRET",
]


def validate_required_env() -> list[str]:
    """Validate and return the list of required environment variables."""

    validate_env(REQUIRED_ENV_VARS)
    return list(REQUIRED_ENV_VARS)


__all__ = ["validate_env", "validate_required_env", "REQUIRED_ENV_VARS"]
