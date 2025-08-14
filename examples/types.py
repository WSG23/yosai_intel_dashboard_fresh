from __future__ import annotations

from typing import Protocol


class BProtocol(Protocol):
    """Protocol representing the behaviour expected by :mod:`examples.A`."""

    def do_b(self) -> str:
        """Return a string representation."""
        ...
