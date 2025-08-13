"""Typed access to environment variables with validation."""

from __future__ import annotations

import os
from typing import Callable, Optional, TypeVar

T = TypeVar("T")


class ConfigError(RuntimeError):
    """Raised when an environment variable is missing or invalid."""


def _coerce(value: str, caster: Callable[[str], T], name: str) -> T:
    """Coerce ``value`` using ``caster`` and wrap errors with ``ConfigError``.

    Args:
        value: Raw string value retrieved from the environment.
        caster: Callable used to convert ``value`` to the desired type.
        name: Name of the environment variable for error reporting.

    Returns:
        The converted value returned by ``caster``.

    Raises:
        ConfigError: If ``caster`` fails to convert the value.
    """

    try:
        return caster(value)
    except (TypeError, ValueError) as exc:
        raise ConfigError(f"Invalid value for {name!r}: {value!r}") from exc


def get_str(name: str, default: Optional[str] = None, required: bool = False) -> str:
    """Retrieve a string environment variable.

    Args:
        name: Name of the environment variable.
        default: Value to return if the variable is not set.
        required: Whether to raise ``ConfigError`` if the variable is missing.

    Returns:
        The environment variable value or ``default`` if unset.

    Raises:
        ConfigError: If ``required`` is ``True`` and the variable is missing.
    """

    v = os.getenv(name, default)
    if required and v is None:
        raise ConfigError(f"Missing required env: {name}")
    return "" if v is None else v


def get_int(name: str, default: Optional[int] = None, required: bool = False) -> int:
    """Retrieve an integer environment variable.

    Args:
        name: Name of the environment variable.
        default: Value to return if the variable is not set.
        required: Whether to raise ``ConfigError`` if the variable is missing.

    Returns:
        The integer value of the environment variable or ``default`` if unset.

    Raises:
        ConfigError: If the variable is required but missing or cannot be cast.
    """

    v = os.getenv(name)
    if v is None:
        if required and default is None:
            raise ConfigError(f"Missing required env: {name}")
        return 0 if default is None else default
    return _coerce(v, int, name)


def get_bool(name: str, default: Optional[bool] = None) -> bool:
    """Retrieve a boolean environment variable.

    Args:
        name: Name of the environment variable.
        default: Value to return if the variable is not set.

    Returns:
        ``True`` if the variable is a truthy string, ``False`` otherwise.
    """

    v = os.getenv(name)
    if v is None:
        return False if default is None else default
    return str(v).strip().lower() in {"1", "true", "t", "yes", "y", "on"}
