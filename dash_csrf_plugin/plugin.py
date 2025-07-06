import logging
from typing import Callable, Dict, List, Optional

import dash

from .config import CSRFConfig, CSRFMode
from .exceptions import CSRFConfigurationError
from .manager import CSRFManager

logger = logging.getLogger(__name__)


class DashCSRFPlugin:
    """Main interface for integrating CSRF protection into Dash apps."""

    def __init__(
        self,
        app: Optional[dash.Dash] = None,
        config: Optional[CSRFConfig] = None,
        mode: CSRFMode = CSRFMode.AUTO,
    ):
        self.app: Optional[dash.Dash] = None
        self.config = config or CSRFConfig()
        self.mode = mode
        self.manager: Optional[CSRFManager] = None
        self._initialized = False
        self._hooks: Dict[str, List[Callable]] = {"before_init": [], "after_init": []}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: dash.Dash) -> None:
        """Initialize the plugin with a Dash application."""
        if not hasattr(app, "server"):
            raise CSRFConfigurationError("Dash app must have a Flask server")

        if self._initialized and self.app is app:
            return

        self.app = app
        self._run_hooks("before_init")

        if self.mode == CSRFMode.AUTO:
            self.mode = self._detect_mode(app)

        self.manager = CSRFManager(app, self.config, self.mode)
        self.manager.init_app()
        self._initialized = True

        if not hasattr(app, "_plugins"):
            app._plugins = {}
        app._plugins["csrf"] = self

        self._run_hooks("after_init")
        logger.info("Dash CSRF Plugin initialized")

    def _detect_mode(self, app: dash.Dash) -> CSRFMode:
        if app.server.config.get("TESTING"):
            return CSRFMode.TESTING
        if app.server.config.get("DEBUG"):
            return CSRFMode.DEVELOPMENT
        return CSRFMode.PRODUCTION

    def add_hook(self, name: str, func: Callable) -> None:
        self._hooks.setdefault(name, []).append(func)

    def _run_hooks(self, name: str) -> None:
        for func in self._hooks.get(name, []):
            try:
                func()
            except Exception as e:
                logger.warning(f"Hook {name} failed: {e}")

    def add_exempt_route(self, route: str) -> None:
        if self.manager:
            self.manager.add_exempt_route(route)

    def add_exempt_view(self, view: str) -> None:
        if self.manager:
            self.manager.add_exempt_view(view)

    def get_csrf_token(self) -> str:
        if self.manager:
            return self.manager.get_csrf_token()
        return ""

    def create_csrf_component(self, component_id: str = "csrf-token"):
        if self.manager:
            return self.manager.create_csrf_component(component_id)
        return None

    def get_status(self) -> Dict[str, str]:
        return {
            "initialized": self._initialized,
            "mode": (
                self.mode.value if isinstance(self.mode, CSRFMode) else str(self.mode)
            ),
        }

    @property
    def is_enabled(self) -> bool:
        return self.manager.is_enabled if self.manager else False
