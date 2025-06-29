#!/usr/bin/env python3
"""
Settings Component - FIXED Callbacks (Simple Version)
"""

import logging
from dataclasses import asdict

try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc, Input, Output, State, callback_context
    from dash.exceptions import PreventUpdate
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False

try:
    from core.unified_callback_coordinator import UnifiedCallbackCoordinator
    from components.ui_settings import SettingsManager, UserSettings, AdminSettings
    IMPORTS_AVAILABLE = True
except ImportError as e:
    print(f"Import error: {e}")
    IMPORTS_AVAILABLE = False

logger = logging.getLogger(__name__)

# =============================================================================
# FIXED CALLBACK FUNCTIONS
# =============================================================================

def toggle_settings_modal(open_clicks, cancel_clicks, is_open):
    """Toggle settings modal"""
    if not any([open_clicks, cancel_clicks]):
        raise PreventUpdate

    if not callback_context.triggered:
        raise PreventUpdate

    button_id = callback_context.triggered[0]["prop_id"].split(".")[0]

    if button_id == "open-settings-btn":
        return True
    elif button_id == "cancel-settings-btn":
        return False

    return False

def save_all_settings(save_clicks, active_tab, theme, language, timezone, 
                     refresh_rate, chart_type, max_records, cache_duration, 
                     audit_days, notification_settings, security_settings,
                     app_port, app_host, logo_height, navbar_height):
    """SINGLE callback for ALL settings - FIXED VERSION"""
    if not save_clicks:
        raise PreventUpdate

    try:
        settings_manager = SettingsManager()

        if active_tab == "user-settings-tab":
            # Save user settings
            user_settings = UserSettings(
                theme=str(theme) if theme else "dark",
                language=str(language) if language else "en",
                timezone=str(timezone) if timezone else "UTC",
                dashboard_refresh_seconds=max(5, min(300, int(refresh_rate or 30))),
                default_chart_type=str(chart_type) if chart_type else "line",
                max_records_display=max(100, min(10000, int(max_records or 1000))),
                analytics_cache_minutes=max(1, min(60, int(cache_duration or 5))),
                audit_trail_days=max(1, min(30, int(audit_days or 7))),
                notifications_enabled="notifications" in (notification_settings or []),
                sound_alerts="sound" in (notification_settings or []),
                auto_refresh_analytics="auto_refresh" in (notification_settings or []),
                show_sensitive_data="sensitive" in (security_settings or []),
                mask_user_ids="mask_ids" in (security_settings or [])
            )

            success = settings_manager.save_user_settings("current_user", user_settings)

            if success:
                return dbc.Alert("User settings saved successfully!", color="success", dismissable=True)
            else:
                return dbc.Alert("Failed to save user settings.", color="danger", dismissable=True)

        elif active_tab == "admin-settings-tab":
            # Save admin settings
            admin_settings = AdminSettings(
                app_port=max(1000, min(65535, int(app_port or 8050))),
                app_host=str(app_host or "127.0.0.1").strip(),
                navbar_logo_height=max(20, min(100, int(logo_height or 46))),
                navbar_height=max(50, min(150, int(navbar_height or 80)))
            )

            success = settings_manager.save_admin_settings(admin_settings)

            if success:
                return dbc.Alert("Admin settings saved successfully!", color="success", dismissable=True)
            else:
                return dbc.Alert("Failed to save admin settings.", color="danger", dismissable=True)

        return dbc.Alert("Please select a settings tab.", color="warning", dismissable=True)

    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return dbc.Alert(f"Error: {str(e)}", color="danger", dismissable=True)

def load_settings_on_open(is_open):
    """Load settings when modal opens"""
    if not is_open:
        raise PreventUpdate

    try:
        settings_manager = SettingsManager()
        user_settings = settings_manager.load_user_settings("current_user")
        admin_settings = settings_manager.load_admin_settings()

        return (asdict(user_settings), asdict(admin_settings))

    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        return (asdict(UserSettings()), asdict(AdminSettings()))

# =============================================================================
# FIXED CALLBACK REGISTRATION - ONE CALLBACK PER OUTPUT
# =============================================================================

def register_settings_callbacks(coordinator: UnifiedCallbackCoordinator) -> None:
    """Register settings callbacks - FIXED VERSION"""

    if not DASH_AVAILABLE or not IMPORTS_AVAILABLE:
        logger.warning("Skipping settings callbacks - dependencies not available")
        return

    try:
        logger.info("Registering settings callbacks...")

        # 1. Modal toggle callback
        coordinator.register_callback(
            Output("settings-modal", "is_open"),
            [Input("open-settings-btn", "n_clicks"), Input("cancel-settings-btn", "n_clicks")],
            [State("settings-modal", "is_open")],
            prevent_initial_call=True,
            callback_id="toggle_settings_modal",
            component_name="settings_component"
        )(toggle_settings_modal)

        # 2. SINGLE save callback for ALL settings - NO CONFLICT
        coordinator.register_callback(
            Output("settings-status-message", "children"),
            [Input("save-settings-btn", "n_clicks")],
            [
                State("settings-tabs", "active_tab"),
                # User settings
                State("user-theme", "value"),
                State("user-language", "value"),
                State("user-timezone", "value"),
                State("user-refresh-rate", "value"),
                State("user-chart-type", "value"),
                State("user-max-records", "value"),
                State("user-cache-duration", "value"),
                State("user-audit-days", "value"),
                State("user-notification-settings", "value"),
                State("user-security-settings", "value"),
                # Admin settings
                State("admin-app-port", "value"),
                State("admin-app-host", "value"),
                State("admin-logo-height", "value"),
                State("admin-navbar-height", "value")
            ],
            prevent_initial_call=True,
            callback_id="save_all_settings",
            component_name="settings_component"
        )(save_all_settings)

        # 3. Load settings callback
        coordinator.register_callback(
            [Output("current-user-settings", "data"), Output("current-admin-settings", "data")],
            [Input("settings-modal", "is_open")],
            prevent_initial_call=True,
            callback_id="load_settings_on_open",
            component_name="settings_component"
        )(load_settings_on_open)

        logger.info("✅ Settings callbacks registered successfully")

    except Exception as e:
        logger.error(f"Failed to register settings callbacks: {e}")
        print(f"Settings callback error: {e}")

__all__ = ["register_settings_callbacks"]

if __name__ == "__main__":
    print("Fixed settings callbacks - replace the unified_settings_callbacks.py file with this content")
