"""Compatibility wrapper for `config.dynamic_config`."""

from __future__ import annotations

import importlib

_mod: object | None = None
__all__: list[str] = []


def _load() -> None:
    global _mod, __all__
    if _mod is None:
        _mod = importlib.import_module("config.dynamic_config")
        __all__ = getattr(
            _mod, "__all__", [n for n in dir(_mod) if not n.startswith("_")]
        )


def __getattr__(name: str) -> object:
    _load()
    return getattr(_mod, name)


def __dir__() -> list[str]:
    _load()
    return __all__
