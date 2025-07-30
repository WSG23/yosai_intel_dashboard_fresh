from __future__ import annotations

"""Upload feature callbacks."""

from core.truly_unified_callbacks import TrulyUnifiedCallbacks


def register_callbacks(app, container) -> None:
    """Register upload callbacks using the provided Dash *app*."""
    callbacks = TrulyUnifiedCallbacks(app)
    callbacks.register_upload_callbacks()
