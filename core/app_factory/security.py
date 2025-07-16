from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - imported for type checking only
    from dash import Dash

from dash_csrf_plugin import CSRFMode, setup_enhanced_csrf_protection

logger = logging.getLogger(__name__)


def initialize_csrf(app: Dash, config_manager: Any) -> None:
    """Initialize CSRF protection if enabled."""
    if (
        config_manager.get_security_config().csrf_enabled
        and config_manager.get_app_config().environment == "production"
    ):
        try:
            app._csrf_plugin = setup_enhanced_csrf_protection(app, CSRFMode.PRODUCTION)
        except Exception as e:  # pragma: no cover - best effort
            logger.warning(f"Failed to initialize CSRF plugin: {e}")


__all__ = ["initialize_csrf", "setup_enhanced_csrf_protection", "CSRFMode"]
