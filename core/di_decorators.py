from __future__ import annotations

"""Lightweight decorators for dependency injection."""

from typing import Any, Callable, TypeVar

T = TypeVar("T")


def injectable(cls: T) -> T:
    """Mark ``cls`` as injectable."""
    setattr(cls, "__injectable__", True)
    return cls


def inject(func: Callable[..., Any]) -> Callable[..., Any]:
    """Mark ``func`` as injectable constructor."""
    setattr(func, "__inject__", True)
    return func
