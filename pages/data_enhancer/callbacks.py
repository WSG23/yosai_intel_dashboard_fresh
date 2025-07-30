from __future__ import annotations

"""Callbacks for the data enhancer feature."""

from core.truly_unified_callbacks import TrulyUnifiedCallbacks


def register_callbacks(app, ICON_PATHS) -> None:
    """Register data enhancer callbacks."""
    callbacks = TrulyUnifiedCallbacks(app)
    # TODO: migrate callbacks from ``services.data_enhancer.app`` to this module.
    # Placeholder to illustrate grouping by feature.
    _ = callbacks  # suppress unused-variable lint
