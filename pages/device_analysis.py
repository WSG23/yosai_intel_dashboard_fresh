import logging
import dash_bootstrap_components as dbc
from dash import html, register_page as dash_register_page

from ui.components.device_components import create_device_mapping_section

logger = logging.getLogger(__name__)


def layout() -> dbc.Container:
    return dbc.Container(
        dbc.Row(
            dbc.Col(
                [
                    html.H2("Device Analysis", className="mb-3"),
                    html.P("Configure or review device mapping for uploaded data", className="text-muted"),
                    create_device_mapping_section(),
                ]
            )
        ),
        fluid=True,
    )


def register_page(app=None) -> None:
    try:
        dash_register_page(__name__, path="/device-analysis", name="Device Analysis", app=app)
    except Exception as e:  # pragma: no cover - best effort
        logger.warning(f"Failed to register page {__name__}: {e}")


def register_callbacks(manager):
    # No custom callbacks beyond those included in components
    pass


__all__ = ["layout", "register_page", "register_callbacks"]
