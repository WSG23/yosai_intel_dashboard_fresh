from __future__ import annotations

from dash import Dash

from yosai_intel_dashboard.src.infrastructure.callbacks.callback_registry import (
    ComponentCallbackManager,
)
from yosai_intel_dashboard.src.infrastructure.callbacks.unified_callbacks import (
    TrulyUnifiedCallbacks,
)


class DemoManager(ComponentCallbackManager):
    registry_name = "demo"

    def __init__(self, registry):
        super().__init__(registry)

    def register_all(self):
        return {}


def test_component_callback_manager_auto_registration():
    app_manual = Dash(__name__)
    coord_manual = TrulyUnifiedCallbacks(app_manual, security_validator=object())
    coord_manual.register_all_callbacks(DemoManager)

    app_auto = Dash(__name__)
    coord_auto = TrulyUnifiedCallbacks(app_auto, security_validator=object())
    coord_auto.register_all_callbacks()

    assert "demo" in ComponentCallbackManager.REGISTRY
    assert coord_manual._namespaces == coord_auto._namespaces
    assert coord_manual.registered_callbacks == coord_auto.registered_callbacks
