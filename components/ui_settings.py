from __future__ import annotations

from typing import Optional
import dash_bootstrap_components as dbc
from dash import html, dcc

from services.settings_service import (
    SettingsManager,
    UserSettings,
    AdminSettings,
)


class SettingsUIBuilder:
    """Builds the settings modal UI"""

    def __init__(self, manager: Optional[SettingsManager] = None) -> None:
        self.manager = manager or SettingsManager()

    # ------------------------------------------------------------------
    def create_settings_modal(self) -> dbc.Modal:
        user = self.manager.load_user_settings()
        admin = self.manager.load_admin_settings()

        return dbc.Modal(
            [
                dbc.ModalHeader(
                    [
                        dbc.ModalTitle("Settings"),
                        dbc.Button(
                            "×",
                            id="settings-modal-close",
                            n_clicks=0,
                            className="btn-close",
                        ),
                    ]
                ),
                dbc.ModalBody(
                    [
                        dbc.Form(
                            [
                                dbc.Label("Site Name"),
                                dbc.Input(
                                    id="admin-site-name",
                                    value=admin.site_name,
                                    type="text",
                                ),
                                dbc.Label("DB Retries", className="mt-2"),
                                dbc.Input(
                                    id="admin-db-retry",
                                    value=admin.db_retry,
                                    type="number",
                                ),
                                dbc.Label("Redis Connections", className="mt-2"),
                                dbc.Input(
                                    id="admin-redis-connections",
                                    value=admin.redis_connections,
                                    type="number",
                                ),
                                html.Hr(),
                                dbc.Label("Theme"),
                                dcc.Dropdown(
                                    id="user-theme",
                                    options=[
                                        {"label": "Light", "value": "light"},
                                        {"label": "Dark", "value": "dark"},
                                    ],
                                    value=user.theme,
                                ),
                                dbc.Label("Language", className="mt-2"),
                                dcc.Dropdown(
                                    id="user-language",
                                    options=[
                                        {"label": "English", "value": "en"},
                                        {"label": "Japanese", "value": "jp"},
                                    ],
                                    value=user.language,
                                ),
                                html.Div(id="settings-save-status", className="mt-2"),
                            ]
                        )
                    ]
                ),
                dbc.ModalFooter(
                    dbc.Button(
                        "Save",
                        id="settings-modal-save",
                        color="primary",
                    )
                ),
            ],
            id="settings-modal",
            is_open=False,
            className="settings-modal",
        )


# Convenience wrapper for callbacks
from services.settings_service import settings_manager as settings_ui_manager
