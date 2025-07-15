from __future__ import annotations


def create_navbar_layout(*_args, **_kwargs):
    """Return a dummy navbar layout, ignoring any parameters."""

    return "navbar"


def register_navbar_callbacks(manager, service=None):
    manager.navbar_registered = True
