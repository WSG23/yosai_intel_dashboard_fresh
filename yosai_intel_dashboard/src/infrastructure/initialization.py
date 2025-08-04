"""Application initialization utilities.

This module provides :class:`ApplicationInitializer` which creates and
verifies the production dependency injection container.  The container is
created through :func:`create_production_container` and cached for reuse.
"""

from __future__ import annotations

from typing import Optional

from yosai_intel_dashboard.src.infrastructure.di.service_container import (
    ServiceContainer,
)
from yosai_intel_dashboard.src.core.di.bootstrap import (
    bootstrap_container as create_production_container,
)


class ApplicationInitializer:
    """Build and verify the application's service container."""

    def __init__(self) -> None:
        self._container: Optional[ServiceContainer] = None

    # ------------------------------------------------------------------
    def get_container(self) -> ServiceContainer:
        """Return a lazily built :class:`ServiceContainer`.

        The container is created only once and reused for subsequent calls.
        """

        if self._container is None:
            self._container = create_production_container()
            self._verify_services()
        return self._container

    # ------------------------------------------------------------------
    def _verify_services(self) -> None:
        """Ensure critical services are registered and resolvable."""

        assert self._container is not None
        required = [
            "config",
            "callback_manager",
            "security_validator",
            "processor",
            "upload_analytics_processor",
        ]

        missing: list[str] = []
        for name in required:
            if not self._container.has(name):
                missing.append(name)
                continue
            try:
                # Attempt to resolve the service to ensure no lazy errors
                self._container.get(name)
            except Exception as exc:  # pragma: no cover - diagnostics only
                missing.append(f"{name}: {exc}")

        if missing:
            raise RuntimeError(
                "Missing required services: " + ", ".join(missing)
            )


# Global initializer instance for convenient import -----------------------
app_initializer = ApplicationInitializer()

__all__ = ["ApplicationInitializer", "app_initializer", "create_production_container"]
