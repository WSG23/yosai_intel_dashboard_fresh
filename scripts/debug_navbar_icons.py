#!/usr/bin/env python3
"""Wrapper to run navbar icon diagnostics."""

from tools.debug.assets import debug_navbar_icons

if __name__ == "__main__":  # pragma: no cover - manual tool
    import sys

    debug_navbar_icons(sys.argv[1:] or None)
