#!/usr/bin/env python3
"""Backward-compatible wrapper for callback diagnostics."""

from tools.debug.callbacks import debug_callback_conflicts, validate_callback_system

if __name__ == "__main__":  # pragma: no cover - manual tool
    debug_callback_conflicts()
    validate_callback_system()
