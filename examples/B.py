from __future__ import annotations

from .types import BProtocol


class B(BProtocol):
    """Simple implementation of :class:`BProtocol`."""

    def do_b(self) -> str:
        return "B"


def create_a() -> A:
    """Create an :class:`A` instance without top-level imports.

    Importing :mod:`examples.A` locally keeps this module importable on its
    own and breaks the circular dependency that would otherwise exist between
    the two modules.
    """

    from .A import A  # Local import to avoid circular dependency

    return A(B())
