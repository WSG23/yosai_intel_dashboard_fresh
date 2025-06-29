#!/usr/bin/env python3
"""
UI Settings Component for Yōsai Intel Dashboard
Main settings interface with user and admin panels
"""

import json
import logging
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime

# Core imports with fallback handling
try:
    import dash_bootstrap_components as dbc
    from dash import html, dcc
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
    class _StubComponent:
        def __init__(self, *args, **kwargs): pass
    dbc = html = dcc = _StubComponent()

logger = logging.getLogger(__name__)

# =============================================================================
# SETTINGS DATA STRUCTURES
# =============================================================================

@dataclass
class UserSettings:
    """User-configurable settings"""
    theme: str = "dark"
    language: str = "en"
    timezone: str = "UTC"
    dashboard_refresh_seconds: int = 30
    notifications_enabled: bool = True
    sound_alerts: bool = False
    default_chart_type: str = "line"
    max_records_display: int = 1000
    auto_refresh_analytics: bool = True
    analytics_cache_minutes: int = 5
    show_sensitive_data: bool = False
    mask_user_ids: bool = True
    audit_trail_days: int = 7

@dataclass  
class AdminSettings:
    """Admin-only configurable settings - All Magic Numbers"""
    # Application Settings
    app_port: int = 8050
    app_host: str = "127.0.0.1" 
    navbar_logo_height: int = 46
    navbar_height: int = 80
    
    # Security Settings
    session_timeout_minutes: int = 120
    pbkdf2_iterations: int = 100000
    rate_limit_requests: int = 100
    rate_limit_window_minutes: int = 1
    max_upload_mb: int = 100
    
    # Database Settings
    db_port: int = 5432
    db_pool_size: int = 10
    db_connection_timeout: int = 30
    db_retry_attempts: int = 3
    
    # Cache Settings
    redis_port: int = 6379
    cache_timeout_seconds: int = 300
    redis_max_connections: int = 20
    
    # Performance Settings
    ai_confidence_threshold: int = 75
    max_records_per_query: int = 50000
    analytics_batch_size: int = 5000
    data_retention_days: int = 365

# =============================================================================
# SETTINGS MANAGER
# =============================================================================

class SettingsManager:
    """Manages settings persistence and validation"""
    
    def __init__(self):
        self.user_settings = UserSettings()
        self.admin_settings = AdminSettings()
    
    def save_user_settings(self, user_id: str, settings: UserSettings) -> bool:
        """Save user settings"""
        try:
            self._validate_user_settings(settings)
            self.user_settings = settings
            logger.info(f"User settings saved for {user_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to save user settings: {e}")
            return False
    
    def load_user_settings(self, user_id: str) -> UserSettings:
        """Load user settings"""
        return self.user_settings
    
    def save_admin_settings(self, settings: AdminSettings) -> bool:
        """Save admin settings"""
        try:
            self._validate_admin_settings(settings)
            self.admin_settings = settings
            logger.info("Admin settings saved successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to save admin settings: {e}")
            return False
    
    def load_admin_settings(self) -> AdminSettings:
        """Load admin settings"""
        return self.admin_settings
    
    def _validate_user_settings(self, settings: UserSettings) -> None:
        """Validate user settings"""
        if settings.dashboard_refresh_seconds < 5:
            raise ValueError("Dashboard refresh must be at least 5 seconds")
        if settings.max_records_display > 10000:
            raise ValueError("Max records display cannot exceed 10,000")
    
    def _validate_admin_settings(self, settings: AdminSettings) -> None:
        """Validate admin settings"""
        if settings.app_port < 1000 or settings.app_port > 65535:
            raise ValueError("Port must be between 1000 and 65535")
        if settings.session_timeout_minutes < 5:
            raise ValueError("Session timeout must be at least 5 minutes")

# =============================================================================
# UI BUILDER
# =============================================================================

class SettingsUIBuilder:
    """Builds UI components for settings management"""
    
    def __init__(self):
        self.settings_manager = SettingsManager()
    
    def create_user_settings_tab(self, current_settings: UserSettings) -> html.Div:
        """Create user settings tab content"""
        if not DASH_AVAILABLE:
            return html.Div("Dash components not available")
        
        return html.Div([
            dbc.Row([
                dbc.Col([
                    html.H5("Display Preferences", className="mb-3"),
                    
                    # Theme Selection
                    html.Div([
                        html.Label("Theme", className="form-label"),
                        dbc.Select(
                            id="user-theme",
                            options=[
                                {"label": "Dark Theme", "value": "dark"},
                                {"label": "Light Theme", "value": "light"},
                                {"label": "Auto (System)", "value": "auto"}
                            ],
                            value=current_settings.theme
                        )
                    ], className="mb-3"),
                    
                    # Language Selection
                    html.Div([
                        html.Label("Language", className="form-label"),
                        dbc.Select(
                            id="user-language",
                            options=[
                                {"label": "English", "value": "en"},
                                {"label": "Japanese", "value": "ja"}
                            ],
                            value=current_settings.language
                        )
                    ], className="mb-3"),
                    
                    # Timezone Selection
                    html.Div([
                        html.Label("Timezone", className="form-label"),
                        dbc.Select(
                            id="user-timezone",
                            options=[
                                {"label": "UTC", "value": "UTC"},
                                {"label": "America/New_York", "value": "America/New_York"},
                                {"label": "America/Los_Angeles", "value": "America/Los_Angeles"},
                                {"label": "Europe/London", "value": "Europe/London"},
                                {"label": "Asia/Tokyo", "value": "Asia/Tokyo"}
                            ],
                            value=current_settings.timezone
                        )
                    ], className="mb-3"),
                    
                    # Dashboard Refresh Rate
                    html.Div([
                        html.Label("Dashboard Refresh Rate (seconds)", className="form-label"),
                        dbc.Input(
                            id="user-refresh-rate",
                            type="number",
                            min=5,
                            max=300,
                            step=5,
                            value=current_settings.dashboard_refresh_seconds
                        ),
                        html.Small("How often to refresh dashboard data (5-300 seconds)", className="text-muted")
                    ], className="mb-3"),
                    
                ], width=6),
                
                dbc.Col([
                    html.H5("Analytics Preferences", className="mb-3"),
                    
                    # Default Chart Type
                    html.Div([
                        html.Label("Default Chart Type", className="form-label"),
                        dbc.Select(
                            id="user-chart-type",
                            options=[
                                {"label": "Line Chart", "value": "line"},
                                {"label": "Bar Chart", "value": "bar"},
                                {"label": "Pie Chart", "value": "pie"},
                                {"label": "Area Chart", "value": "area"}
                            ],
                            value=current_settings.default_chart_type
                        )
                    ], className="mb-3"),
                    
                    # Max Records Display
                    html.Div([
                        html.Label("Max Records to Display", className="form-label"),
                        dbc.Input(
                            id="user-max-records",
                            type="number",
                            min=100,
                            max=10000,
                            step=100,
                            value=current_settings.max_records_display
                        ),
                        html.Small("Maximum records to show in tables and charts", className="text-muted")
                    ], className="mb-3"),
                    
                    # Analytics Cache Duration
                    html.Div([
                        html.Label("Analytics Cache Duration (minutes)", className="form-label"),
                        dbc.Input(
                            id="user-cache-duration",
                            type="number",
                            min=1,
                            max=60,
                            step=1,
                            value=current_settings.analytics_cache_minutes
                        ),
                        html.Small("How long to cache analytics results", className="text-muted")
                    ], className="mb-3"),
                    
                    # Notification Settings
                    html.H6("Notifications", className="mt-4 mb-2"),
                    dbc.Checklist(
                        id="user-notification-settings",
                        options=[
                            {"label": "Enable Notifications", "value": "notifications"},
                            {"label": "Sound Alerts", "value": "sound"},
                            {"label": "Auto-refresh Analytics", "value": "auto_refresh"}
                        ],
                        value=[
                            opt for opt, enabled in [
                                ("notifications", current_settings.notifications_enabled),
                                ("sound", current_settings.sound_alerts),
                                ("auto_refresh", current_settings.auto_refresh_analytics)
                            ] if enabled
                        ],
                        inline=False
                    ),
                    
                ], width=6)
            ]),
            
            html.Hr(),
            
            # Security Display Settings
            dbc.Row([
                dbc.Col([
                    html.H5("Security Display", className="mb-3"),
                    
                    html.Div([
                        html.Label("Audit Trail Duration (days)", className="form-label"),
                        dbc.Input(
                            id="user-audit-days",
                            type="number",
                            min=1,
                            max=30,
                            step=1,
                            value=current_settings.audit_trail_days
                        ),
                        html.Small("How many days of audit trail to show", className="text-muted")
                    ], className="mb-3"),
                    
                    dbc.Checklist(
                        id="user-security-settings",
                        options=[
                            {"label": "Show Sensitive Data", "value": "sensitive"},
                            {"label": "Mask User IDs", "value": "mask_ids"}
                        ],
                        value=[
                            opt for opt, enabled in [
                                ("sensitive", current_settings.show_sensitive_data),
                                ("mask_ids", current_settings.mask_user_ids)
                            ] if enabled
                        ],
                        inline=False
                    ),
                    
                ], width=6)
            ])
        ])
    
    def create_admin_settings_tab(self, current_settings: AdminSettings) -> html.Div:
        """Create admin settings tab content with all magic numbers"""
        if not DASH_AVAILABLE:
            return html.Div("Dash components not available")
        
        return html.Div([
            dbc.Accordion([
                
                # Application Settings
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label("Application Port", className="form-label"),
                                dbc.Input(
                                    id="admin-app-port",
                                    type="number",
                                    min=1000,
                                    max=65535,
                                    value=current_settings.app_port
                                ),
                                html.Small("Port for the web application (1000-65535)", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Application Host", className="form-label"),
                                dbc.Input(
                                    id="admin-app-host",
                                    type="text",
                                    value=current_settings.app_host
                                ),
                                html.Small("Host address to bind to (0.0.0.0 for all interfaces)", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Navbar Logo Height (px)", className="form-label"),
                                dbc.Input(
                                    id="admin-logo-height",
                                    type="number",
                                    min=20,
                                    max=100,
                                    value=current_settings.navbar_logo_height
                                ),
                                html.Small("Height of logo in navigation bar", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6),
                        
                        dbc.Col([
                            html.Div([
                                html.Label("Navbar Height (px)", className="form-label"),
                                dbc.Input(
                                    id="admin-navbar-height",
                                    type="number",
                                    min=50,
                                    max=150,
                                    value=current_settings.navbar_height
                                ),
                                html.Small("Total height of navigation bar", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6)
                    ])
                ], title="Application Settings"),
                
                # Security Settings
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label("Session Timeout (minutes)", className="form-label"),
                                dbc.Input(
                                    id="admin-session-timeout",
                                    type="number",
                                    min=5,
                                    max=1440,
                                    value=current_settings.session_timeout_minutes
                                ),
                                html.Small("User session timeout in minutes", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("PBKDF2 Iterations", className="form-label"),
                                dbc.Input(
                                    id="admin-pbkdf2-iterations",
                                    type="number",
                                    min=10000,
                                    max=1000000,
                                    step=10000,
                                    value=current_settings.pbkdf2_iterations
                                ),
                                html.Small("Password hashing iterations (higher = more secure, slower)", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Rate Limit Requests", className="form-label"),
                                dbc.Input(
                                    id="admin-rate-limit-requests",
                                    type="number",
                                    min=10,
                                    max=10000,
                                    value=current_settings.rate_limit_requests
                                ),
                                html.Small("Requests allowed per time window", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6),
                        
                        dbc.Col([
                            html.Div([
                                html.Label("Rate Limit Window (minutes)", className="form-label"),
                                dbc.Input(
                                    id="admin-rate-limit-window",
                                    type="number",
                                    min=1,
                                    max=60,
                                    value=current_settings.rate_limit_window_minutes
                                ),
                                html.Small("Time window for rate limiting", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Max Upload Size (MB)", className="form-label"),
                                dbc.Input(
                                    id="admin-max-upload",
                                    type="number",
                                    min=1,
                                    max=1000,
                                    value=current_settings.max_upload_mb
                                ),
                                html.Small("Maximum file upload size", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6)
                    ])
                ], title="Security Settings"),
                
                # Database Settings
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label("Database Port", className="form-label"),
                                dbc.Input(
                                    id="admin-db-port",
                                    type="number",
                                    min=1000,
                                    max=65535,
                                    value=current_settings.db_port
                                ),
                                html.Small("PostgreSQL database port", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Connection Pool Size", className="form-label"),
                                dbc.Input(
                                    id="admin-db-pool-size",
                                    type="number",
                                    min=1,
                                    max=100,
                                    value=current_settings.db_pool_size
                                ),
                                html.Small("Number of database connections to maintain", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6),
                        
                        dbc.Col([
                            html.Div([
                                html.Label("Connection Timeout (seconds)", className="form-label"),
                                dbc.Input(
                                    id="admin-db-timeout",
                                    type="number",
                                    min=5,
                                    max=300,
                                    value=current_settings.db_connection_timeout
                                ),
                                html.Small("Database connection timeout", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Retry Attempts", className="form-label"),
                                dbc.Input(
                                    id="admin-db-retry",
                                    type="number",
                                    min=0,
                                    max=10,
                                    value=current_settings.db_retry_attempts
                                ),
                                html.Small("Number of connection retry attempts", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6)
                    ])
                ], title="Database Settings"),
                
                # Cache Settings
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label("Redis Port", className="form-label"),
                                dbc.Input(
                                    id="admin-redis-port",
                                    type="number",
                                    min=1000,
                                    max=65535,
                                    value=current_settings.redis_port
                                ),
                                html.Small("Redis server port", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Cache Timeout (seconds)", className="form-label"),
                                dbc.Input(
                                    id="admin-cache-timeout",
                                    type="number",
                                    min=30,
                                    max=3600,
                                    value=current_settings.cache_timeout_seconds
                                ),
                                html.Small("Default cache expiration time", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6),
                        
                        dbc.Col([
                            html.Div([
                                html.Label("Redis Max Connections", className="form-label"),
                                dbc.Input(
                                    id="admin-redis-connections",
                                    type="number",
                                    min=1,
                                    max=100,
                                    value=current_settings.redis_max_connections
                                ),
                                html.Small("Maximum Redis connections", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6)
                    ])
                ], title="Cache Settings"),
                
                # Performance Settings
                dbc.AccordionItem([
                    dbc.Row([
                        dbc.Col([
                            html.Div([
                                html.Label("Max Records Per Query", className="form-label"),
                                dbc.Input(
                                    id="admin-max-records",
                                    type="number",
                                    min=1000,
                                    max=1000000,
                                    step=1000,
                                    value=current_settings.max_records_per_query
                                ),
                                html.Small("Maximum records returned by analytics queries", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Analytics Batch Size", className="form-label"),
                                dbc.Input(
                                    id="admin-batch-size",
                                    type="number",
                                    min=100,
                                    max=10000,
                                    step=100,
                                    value=current_settings.analytics_batch_size
                                ),
                                html.Small("Records processed in each batch", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6),
                        
                        dbc.Col([
                            html.Div([
                                html.Label("AI Confidence Threshold (%)", className="form-label"),
                                dbc.Input(
                                    id="admin-ai-threshold",
                                    type="number",
                                    min=0,
                                    max=100,
                                    value=current_settings.ai_confidence_threshold
                                ),
                                html.Small("Minimum confidence for AI predictions", className="text-muted")
                            ], className="mb-3"),
                            
                            html.Div([
                                html.Label("Data Retention Days", className="form-label"),
                                dbc.Input(
                                    id="admin-data-retention",
                                    type="number",
                                    min=1,
                                    max=3650,
                                    value=current_settings.data_retention_days
                                ),
                                html.Small("Days to retain data before archival", className="text-muted")
                            ], className="mb-3"),
                            
                        ], width=6)
                    ])
                ], title="Performance Settings"),
                
            ], start_collapsed=True)
        ])
    
    def create_settings_modal(self, user_role: str = "user") -> dbc.Modal:
        """Create the main settings modal"""
        if not DASH_AVAILABLE:
            return html.Div("Dash components not available")
        
        # Load current settings
        user_settings = self.settings_manager.load_user_settings("current_user")
        admin_settings = self.settings_manager.load_admin_settings()
        
        # Create tabs based on user role
        tabs = [
            dbc.Tab(
                self.create_user_settings_tab(user_settings),
                label="User Settings",
                tab_id="user-settings-tab"
            )
        ]
        
        if user_role == "admin":
            tabs.append(
                dbc.Tab(
                    self.create_admin_settings_tab(admin_settings),
                    label="Admin Settings",
                    tab_id="admin-settings-tab"
                )
            )
        
        return dbc.Modal([
            dbc.ModalHeader([
                dbc.ModalTitle("Dashboard Settings")
            ]),
            dbc.ModalBody([
                dbc.Tabs(tabs, id="settings-tabs", active_tab="user-settings-tab"),
                html.Div(id="settings-status-message", className="mt-3"),
                dcc.Store(id="current-user-settings", data=asdict(user_settings)),
                dcc.Store(id="current-admin-settings", data=asdict(admin_settings)),
            ]),
            dbc.ModalFooter([
                dbc.Button("Save Changes", id="save-settings-btn", color="primary", className="me-2"),
                dbc.Button("Reset to Defaults", id="reset-settings-btn", color="warning", className="me-2"),
                dbc.Button("Cancel", id="cancel-settings-btn", color="secondary")
            ])
        ], id="settings-modal", size="xl", is_open=False)

# Export classes
__all__ = ["SettingsUIBuilder", "SettingsManager", "UserSettings", "AdminSettings"]
