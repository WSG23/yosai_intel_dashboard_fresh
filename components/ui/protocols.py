from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NavbarFactoryProtocol(Protocol):
    """Factory responsible for providing an app for navbar helpers."""

    def create_app(self) -> Any:
        """Return an application instance with asset access methods."""
        ...

    def get_icon_url(self, app: Any, name: str) -> str | None:
        """Return an asset URL for *name* or ``None`` if unavailable."""
        ...
