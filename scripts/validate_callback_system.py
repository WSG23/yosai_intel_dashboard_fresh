#!/usr/bin/env python3
"""Wrapper to run callback diagnostics."""

from tools.debug.callbacks import debug_callback_conflicts, validate_callback_system

if __name__ == "__main__":  # pragma: no cover - manual tool
    print("\U0001f50d Validating callback system and dependencies...")
    ok_callbacks = validate_callback_system()
    debug_callback_conflicts()
    if ok_callbacks:
        print("\U0001f389 Diagnostics completed successfully!")
    else:
        print("\U0001f4a5 Issues found - check logs above")
