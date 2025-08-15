"""Test stub for navbar component.

This module provides minimal stand-ins for the real navbar implementation so
tests can import and use basic functionality without pulling in the full UI
stack.
"""

from __future__ import annotations


class Navbar:
    """Minimal placeholder navbar used in tests."""

    def render(self) -> str:
        """Return mock HTML for the navbar."""

        return "<nav>navbar</nav>"


def create_navbar_layout(*_args, **_kwargs) -> str:
    """Return a dummy navbar layout, ignoring any parameters."""

    return Navbar().render()


def register_navbar_callbacks(manager, service=None) -> None:
    """Record that navbar callbacks were registered."""

    manager.navbar_registered = True


__all__ = ["Navbar", "create_navbar_layout", "register_navbar_callbacks"]

