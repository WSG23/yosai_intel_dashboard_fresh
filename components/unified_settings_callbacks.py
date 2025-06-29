#!/usr/bin/env python3
"""
Settings Component - Unified Callback System Integration
Callbacks designed to work with the existing UnifiedCallbackCoordinator
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import asdict

# Core imports with fallback handling
try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc, Input, Output, State, ALL, MATCH, ctx
    from dash.exceptions import PreventUpdate
    DASH_AVAILABLE = True
except ImportError:
    print("Warning: Dash components not available")
    DASH_AVAILABLE = False

# Local imports
from core.unified_callback_coordinator import UnifiedCallbackCoordinator
from components.ui_settings import (
    SettingsManager, UserSettings, AdminSettings, SettingsUIBuilder
)

logger = logging.getLogger(__name__)

# =============================================================================
# SETTINGS CALLBACK FUNCTIONS
# =============================================================================

def toggle_settings_modal(open_clicks, cancel_clicks, save_clicks, is_open):
    """Toggle settings modal visibility"""
    try:
        if not any([open_clicks, cancel_clicks, save_clicks]):
            raise PreventUpdate
        
        if not ctx.triggered:
            raise PreventUpdate
        
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        logger.debug(f"Settings modal button triggered: {button_id}")
        
        if button_id == "open-settings-btn" and open_clicks:
            logger.info("Opening settings modal")
            return True
        elif button_id in ["cancel-settings-btn", "settings-modal-close"]:
            logger.info("Closing settings modal")
            return False
        elif button_id == "save-settings-btn":
            # Keep modal open after save to show status
            return is_open
        
        return not is_open
        
    except Exception as e:
        logger.error(f"Error in toggle_settings_modal: {e}")
        return False

def save_user_settings_callback(save_clicks, active_tab, theme, language, timezone, 
                               refresh_rate, chart_type, max_records, cache_duration, 
                               audit_days, notification_settings, security_settings):
    """Save user settings"""
    try:
        if not save_clicks:
            raise PreventUpdate
        
        if active_tab != "user-settings-tab":
            raise PreventUpdate
        
        # Sanitize inputs
        theme = str(theme) if theme else "dark"
        language = str(language) if language else "en"
        timezone = str(timezone) if timezone else "UTC"
        chart_type = str(chart_type) if chart_type else "line"
        
        # Validate numeric inputs
        refresh_rate = max(5, min(300, int(refresh_rate or 30)))
        max_records = max(100, min(10000, int(max_records or 1000)))
        cache_duration = max(1, min(60, int(cache_duration or 5)))
        audit_days = max(1, min(30, int(audit_days or 7)))
        
        # Process checkbox values
        notification_settings = notification_settings or []
        security_settings = security_settings or []
        
        # Create user settings object
        user_settings = UserSettings(
            theme=theme,
            language=language,
            timezone=timezone,
            dashboard_refresh_seconds=refresh_rate,
            default_chart_type=chart_type,
            max_records_display=max_records,
            analytics_cache_minutes=cache_duration,
            audit_trail_days=audit_days,
            notifications_enabled="notifications" in notification_settings,
            sound_alerts="sound" in notification_settings,
            auto_refresh_analytics="auto_refresh" in notification_settings,
            show_sensitive_data="sensitive" in security_settings,
            mask_user_ids="mask_ids" in security_settings
        )
        
        # Save settings
        settings_manager = SettingsManager()
        success = settings_manager.save_user_settings("current_user", user_settings)
        
        if success:
            logger.info("User settings saved successfully")
            return dbc.Alert(
                "User settings saved successfully!", 
                color="success",
                dismissable=True,
                duration=4000
            )
        else:
            logger.error("Failed to save user settings")
            return dbc.Alert(
                "Failed to save user settings. Please try again.", 
                color="danger",
                dismissable=True
            )
            
    except ValueError as e:
        logger.error(f"Validation error in save_user_settings: {e}")
        return dbc.Alert(
            f"Invalid input: {str(e)}", 
            color="warning",
            dismissable=True
        )
    except Exception as e:
        logger.error(f"Error in save_user_settings_callback: {e}")
        return dbc.Alert(
            f"Unexpected error: {str(e)}", 
            color="danger",
            dismissable=True
        )

def save_admin_settings_callback(save_clicks, active_tab, app_port, app_host, 
                                logo_height, navbar_height, session_timeout,
                                pbkdf2_iterations, rate_limit_requests, rate_limit_window,
                                db_port, db_pool_size, db_timeout, redis_port,
                                cache_timeout, max_upload, max_records, batch_size,
                                ai_threshold, data_retention):
    """Save admin settings"""
    try:
        if not save_clicks:
            raise PreventUpdate
        
        if active_tab != "admin-settings-tab":
            raise PreventUpdate
        
        # Validate and sanitize admin inputs
        app_port = max(1000, min(65535, int(app_port or 8050)))
        app_host = str(app_host or "127.0.0.1").strip()
        logo_height = max(20, min(100, int(logo_height or 46)))
        navbar_height = max(50, min(150, int(navbar_height or 80)))
        session_timeout = max(5, min(1440, int(session_timeout or 120)))
        pbkdf2_iterations = max(10000, min(1000000, int(pbkdf2_iterations or 100000)))
        rate_limit_requests = max(10, min(10000, int(rate_limit_requests or 100)))
        rate_limit_window = max(1, min(60, int(rate_limit_window or 1)))
        db_port = max(1000, min(65535, int(db_port or 5432)))
        db_pool_size = max(1, min(100, int(db_pool_size or 10)))
        db_timeout = max(5, min(300, int(db_timeout or 30)))
        redis_port = max(1000, min(65535, int(redis_port or 6379)))
        cache_timeout = max(30, min(3600, int(cache_timeout or 300)))
        max_upload = max(1, min(1000, int(max_upload or 100)))
        max_records = max(1000, min(1000000, int(max_records or 50000)))
        batch_size = max(100, min(10000, int(batch_size or 5000)))
        ai_threshold = max(0, min(100, int(ai_threshold or 75)))
        data_retention = max(1, min(3650, int(data_retention or 365)))
        
        # Create admin settings object with validated values
        admin_settings = AdminSettings(
            app_port=app_port,
            app_host=app_host,
            navbar_logo_height=logo_height,
            navbar_height=navbar_height,
            session_timeout_minutes=session_timeout,
            pbkdf2_iterations=pbkdf2_iterations,
            rate_limit_requests=rate_limit_requests,
            rate_limit_window_minutes=rate_limit_window,
            db_port=db_port,
            db_pool_size=db_pool_size,
            db_connection_timeout=db_timeout,
            redis_port=redis_port,
            cache_timeout_seconds=cache_timeout,
            max_upload_mb=max_upload,
            max_records_per_query=max_records,
            analytics_batch_size=batch_size,
            ai_confidence_threshold=ai_threshold,
            data_retention_days=data_retention
        )
        
        # Save admin settings
        settings_manager = SettingsManager()
        success = settings_manager.save_admin_settings(admin_settings)
        
        if success:
            logger.info("Admin settings saved successfully")
            return dbc.Alert([
                "Admin settings saved successfully! ",
                html.Br(),
                html.Small("Some changes may require an application restart to take effect.", 
                          style={"fontStyle": "italic"})
            ], color="success", dismissable=True, duration=6000)
        else:
            logger.error("Failed to save admin settings")
            return dbc.Alert(
                "Failed to save admin settings. Please check permissions and try again.", 
                color="danger",
                dismissable=True
            )
            
    except ValueError as e:
        logger.error(f"Validation error in save_admin_settings: {e}")
        return dbc.Alert(
            f"Invalid input: {str(e)}", 
            color="warning",
            dismissable=True
        )
    except Exception as e:
        logger.error(f"Error in save_admin_settings_callback: {e}")
        return dbc.Alert(
            f"Unexpected error: {str(e)}", 
            color="danger",
            dismissable=True
        )

def load_settings_on_modal_open(is_open):
    """Load current settings when modal opens"""
    try:
        if not is_open:
            raise PreventUpdate
        
        # Load current settings
        settings_manager = SettingsManager()
        user_settings = settings_manager.load_user_settings("current_user")
        admin_settings = settings_manager.load_admin_settings()
        
        return (
            asdict(user_settings),
            asdict(admin_settings)
        )
        
    except Exception as e:
        logger.error(f"Error loading settings: {e}")
        # Return defaults on error
        return (
            asdict(UserSettings()),
            asdict(AdminSettings())
        )

# =============================================================================
# CALLBACK REGISTRATION WITH UNIFIED COORDINATOR
# =============================================================================

def register_settings_callbacks(coordinator: UnifiedCallbackCoordinator) -> None:
    """Register all settings callbacks using the UnifiedCallbackCoordinator"""
    if not DASH_AVAILABLE:
        logger.warning("Dash not available, skipping settings callback registration")
        return
    
    try:
        logger.info("Registering settings component callbacks...")
        
        # Modal toggle callback
        coordinator.register_callback(
            Output("settings-modal", "is_open"),
            [
                Input("open-settings-btn", "n_clicks"),
                Input("cancel-settings-btn", "n_clicks"),
                Input("save-settings-btn", "n_clicks")
            ],
            [State("settings-modal", "is_open")],
            prevent_initial_call=True,
            callback_id="toggle_settings_modal",
            component_name="settings_component"
        )(toggle_settings_modal)
        
        # Save user settings callback
        coordinator.register_callback(
            Output("settings-status-message", "children"),
            [Input("save-settings-btn", "n_clicks")],
            [
                State("settings-tabs", "active_tab"),
                State("user-theme", "value"),
                State("user-language", "value"),
                State("user-timezone", "value"),
                State("user-refresh-rate", "value"),
                State("user-chart-type", "value"),
                State("user-max-records", "value"),
                State("user-cache-duration", "value"),
                State("user-audit-days", "value"),
                State("user-notification-settings", "value"),
                State("user-security-settings", "value")
            ],
            prevent_initial_call=True,
            callback_id="save_user_settings",
            component_name="settings_component"
        )(save_user_settings_callback)
        
        # Save admin settings callback  
        coordinator.register_callback(
            Output("settings-status-message", "children", allow_duplicate=True),
            [Input("save-settings-btn", "n_clicks")],
            [
                State("settings-tabs", "active_tab"),
                State("admin-app-port", "value"),
                State("admin-app-host", "value"),
                State("admin-logo-height", "value"),
                State("admin-navbar-height", "value"),
                State("admin-session-timeout", "value"),
                State("admin-pbkdf2-iterations", "value"),
                State("admin-rate-limit-requests", "value"),
                State("admin-rate-limit-window", "value"),
                State("admin-db-port", "value"),
                State("admin-db-pool-size", "value"),
                State("admin-db-timeout", "value"),
                State("admin-redis-port", "value"),
                State("admin-cache-timeout", "value"),
                State("admin-max-upload", "value"),
                State("admin-max-records", "value"),
                State("admin-batch-size", "value"),
                State("admin-ai-threshold", "value"),
                State("admin-data-retention", "value")
            ],
            prevent_initial_call=True,
            callback_id="save_admin_settings",
            component_name="settings_component"
        )(save_admin_settings_callback)
        
        # Load settings when modal opens
        coordinator.register_callback(
            [
                Output("current-user-settings", "data"),
                Output("current-admin-settings", "data")
            ],
            [Input("settings-modal", "is_open")],
            prevent_initial_call=True,
            callback_id="load_settings_on_open",
            component_name="settings_component"
        )(load_settings_on_modal_open)
        
        logger.info("Settings component callbacks registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to register settings callbacks: {e}")
        raise

# Export registration function
__all__ = ["register_settings_callbacks"]
