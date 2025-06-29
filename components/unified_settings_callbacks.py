import dash
from dash import callback_context
from dash.dependencies import Input, Output, State

from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from services.settings_service import AdminSettings
from .ui_settings import settings_ui_manager


def toggle_settings_modal(open_clicks, close_clicks, save_clicks, is_open):
    ctx = callback_context
    if not ctx.triggered:
        return is_open
    trigger = ctx.triggered[0]["prop_id"].split(".")[0]
    if trigger == "open-settings-btn":
        return True
    if trigger in {"settings-modal-close", "settings-modal-save"}:
        return False
    return is_open


def save_admin_settings_callback(n_clicks, site_name, db_retry, redis_connections):
    if not n_clicks:
        raise dash.exceptions.PreventUpdate

    try:
        retry = int(db_retry) if db_retry is not None else 0
    except ValueError:
        retry = 0
    try:
        redis_conns = int(redis_connections) if redis_connections is not None else 0
    except ValueError:
        redis_conns = 0

    settings = AdminSettings(
        site_name=site_name or "",
        db_retry=retry,
        redis_connections=redis_conns,
    )
    settings_ui_manager.save_admin_settings(settings)
    return "Settings saved"


def register_settings_callbacks(manager: UnifiedCallbackCoordinator) -> None:
    manager.register_callback(
        Output("settings-modal", "is_open"),
        [
            Input("open-settings-btn", "n_clicks"),
            Input("settings-modal-close", "n_clicks"),
            Input("settings-modal-save", "n_clicks"),
        ],
        [State("settings-modal", "is_open")],
        prevent_initial_call=True,
        callback_id="toggle_settings_modal",
        component_name="settings",
    )(toggle_settings_modal)

    manager.register_callback(
        Output("settings-save-status", "children"),
        Input("settings-modal-save", "n_clicks"),
        [
            State("admin-site-name", "value"),
            State("admin-db-retry", "value"),
            State("admin-redis-connections", "value"),
        ],
        prevent_initial_call=True,
        callback_id="save_admin_settings",
        component_name="settings",
    )(save_admin_settings_callback)


__all__ = ["register_settings_callbacks"]
