from __future__ import annotations

"""Device learning feature callbacks."""

from core.truly_unified_callbacks import TrulyUnifiedCallbacks
from services.device_learning_service import create_learning_callbacks


def register_callbacks(app, ICON_PATHS) -> None:
    """Register device learning callbacks."""
    callbacks = TrulyUnifiedCallbacks(app)
    create_learning_callbacks(callbacks)
