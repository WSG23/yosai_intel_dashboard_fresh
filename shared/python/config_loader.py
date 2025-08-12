from __future__ import annotations
import os
from typing import Callable, Optional, TypeVar

T = TypeVar("T")

class ConfigError(RuntimeError):
    pass


def _coerce(value: str, caster: Callable[[str], T], name: str) -> T:
    try:
        return caster(value)
    except Exception as e:
        raise ConfigError(f"Invalid value for {name!r}: {value!r}") from e


def get_str(name: str, default: Optional[str] = None, required: bool = False) -> str:
    v = os.getenv(name, default)
    if required and v is None:
        raise ConfigError(f"Missing required env: {name}")
    return "" if v is None else v


def get_int(name: str, default: Optional[int] = None, required: bool = False) -> int:
    v = os.getenv(name)
    if v is None:
        if required and default is None:
            raise ConfigError(f"Missing required env: {name}")
        return 0 if default is None else default
    return _coerce(v, int, name)


def get_bool(name: str, default: Optional[bool] = None) -> bool:
    v = os.getenv(name)
    if v is None:
        return False if default is None else default
    return str(v).strip().lower() in {"1", "true", "t", "yes", "y", "on"}
