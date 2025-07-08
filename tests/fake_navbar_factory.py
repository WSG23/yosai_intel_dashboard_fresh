from __future__ import annotations

from typing import Any

from components.ui.protocols import NavbarFactoryProtocol


class _FakeApp:
    """Simple application stub providing asset URLs."""

    def get_asset_url(self, path: str) -> str:
        return f"/assets/{path}"


class FakeNavbarFactory(NavbarFactoryProtocol):
    def create_app(self) -> Any:
        return _FakeApp()

    def get_icon_url(self, app: Any, name: str) -> str | None:
        return f"/assets/navbar_icons/{name}.png"
