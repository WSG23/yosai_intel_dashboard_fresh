from __future__ import annotations


def create_navbar_layout():
    return "navbar"


def register_navbar_callbacks(manager, service=None):
    manager.navbar_registered = True
