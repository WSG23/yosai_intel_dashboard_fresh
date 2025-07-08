from __future__ import annotations

from typing import Any

from components.ui.protocols import NavbarFactoryProtocol


class _TestApp:
    def get_asset_url(self, path: str) -> str:
        return f"/assets/{path}"


class TestNavbarFactory(NavbarFactoryProtocol):
    """Provide a simple application for navbar helpers."""

    def create_app(self) -> Any:
        return _TestApp()

    def get_icon_url(self, app: Any, name: str) -> str | None:
        return f"/assets/navbar_icons/{name}.png"
