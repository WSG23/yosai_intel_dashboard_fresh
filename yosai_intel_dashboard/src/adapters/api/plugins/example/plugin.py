"""Minimal working example plugin."""

from __future__ import annotations

from dataclasses import dataclass

from dash import Input, Output
from dash.exceptions import PreventUpdate

from core.protocols.plugin import CallbackPluginProtocol, PluginMetadata


@dataclass
class GreetingService:
    greeting: str = "Hello"

    def greet(self, name: str) -> str:
        return f"{self.greeting}, {name}!"


class ExamplePlugin(CallbackPluginProtocol):
    """Simple plugin demonstrating DI and callback hooks."""

    metadata = PluginMetadata(
        name="example",
        version="1.0.0",
        description="Minimal example plugin",
        author="Example",
    )

    def __init__(self) -> None:
        self.service: GreetingService | None = None

    # --------------------------------------------------------------
    def load(self, container, config: dict) -> bool:
        """Register the service with the DI container."""
        self.service = GreetingService(config.get("greeting", "Hello"))
        container.register("greeting_service", self.service)
        return True

    # --------------------------------------------------------------
    def configure(self, config: dict) -> bool:
        return True

    # --------------------------------------------------------------
    def start(self) -> bool:
        return True

    # --------------------------------------------------------------
    def stop(self) -> bool:
        return True

    # --------------------------------------------------------------
    def health_check(self) -> dict:
        return {"healthy": True}

    # --------------------------------------------------------------
    def register_callbacks(self, manager, container) -> bool:
        """Example callback using the registered service."""
        svc: GreetingService = container.get("greeting_service")

        @manager.unified_callback(
            Output("greet-output", "children"),
            Input("name-input", "value"),
            callback_id="example_greet",
            component_name="example_plugin",
        )
        def _greet(name: str | None) -> str:
            if not name:
                raise PreventUpdate
            return svc.greet(name)

        return True


def create_plugin() -> ExamplePlugin:
    """Factory used by PluginManager."""
    return ExamplePlugin()
