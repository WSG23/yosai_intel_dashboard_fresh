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


__all__ = ["validate_env"]
