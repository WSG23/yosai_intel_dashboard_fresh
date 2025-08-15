from __future__ import annotations

import sys
import textwrap
from contextlib import AbstractContextManager
from pathlib import Path


class PluginPackageBuilder(AbstractContextManager):
    """Helper to create a temporary plugin package for tests."""

    def __init__(
        self,
        base_dir: Path,
        package_name: str = "auto_pkg",
        plugin_name: str = "auto_plugin",
        version: str = "0.1",
        description: str = "auto plugin",
        author: str = "tester",
        callback_id: str = "auto_cb",
    ) -> None:
        self.base_dir = Path(base_dir)
        self._package_name = package_name
        self._plugin_name = plugin_name
        self.version = version
        self.description = description
        self.author = author
        self._callback_id = callback_id
        self._pkg_path = self.base_dir / self._package_name

    # path of the created package
    @property
    def package_path(self) -> Path:
        return self._pkg_path

    @property
    def package_name(self) -> str:
        return self._package_name

    @property
    def plugin_name(self) -> str:
        return self._plugin_name

    @property
    def callback_id(self) -> str:
        return self._callback_id

    def _write_files(self) -> None:
        self._pkg_path.mkdir()
        (self._pkg_path / "__init__.py").write_text("")
        plugin_code = f"""
from dash import Output, Input
from yosai_intel_dashboard.src.core.protocols.plugin import PluginMetadata
from yosai_intel_dashboard.src.core.plugins.callback_unifier import CallbackUnifier

class AutoPlugin:
    metadata = PluginMetadata(
        name="{self._plugin_name}",
        version="{self.version}",
        description="{self.description}",
        author="{self.author}",
    )

    def __init__(self):
        self.callback_registered = False

    def load(self, container, config):
        container.register("auto_service", "ok")
        return True

    def configure(self, config):
        return True

    def start(self):
        return True

    def stop(self):
        return True

    def health_check(self):
        return {{"healthy": True}}

    def register_callbacks(self, manager, container):
        @CallbackUnifier(manager)(
            Output("out", "children"),
            Input("in", "value"),
            callback_id="{self._callback_id}",
            component_name="AutoPlugin",
        )
        def cb(value):
            return f"auto:{{value}}"

        self.callback_registered = True
        return True

def create_plugin():
    return AutoPlugin()
"""
        (self._pkg_path / "plug.py").write_text(textwrap.dedent(plugin_code))

    def __enter__(self) -> "PluginPackageBuilder":
        self._write_files()
        sys.path.insert(0, str(self.base_dir))
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if str(self.base_dir) in sys.path:
            sys.path.remove(str(self.base_dir))
        # do not suppress exceptions
        return None
