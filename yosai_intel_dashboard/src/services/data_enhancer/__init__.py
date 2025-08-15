"""
Lightweight init to avoid importing UI code in non-UI contexts (e.g., API).
Exports run_data_enhancer lazily so the module doesn't pull in Dash at import-time.
"""

from __future__ import annotations

__all__ = ["run_data_enhancer"]

def run_data_enhancer(*args, **kwargs):
    # Import only when actually needed (e.g., CLI entry), not at API startup.
    from .cli import run_data_enhancer as _run
    return _run(*args, **kwargs)
