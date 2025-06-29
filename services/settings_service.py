from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
import json

from config.config import get_database_config
from config.database_manager import DatabaseManager


@dataclass
class UserSettings:
    """User specific settings"""
    theme: str = "light"
    language: str = "en"


@dataclass
class AdminSettings:
    """Administrative settings"""
    site_name: str = "Yosai Dashboard"
    db_retry: int = 0
    redis_connections: int = 0


class SettingsPersistenceService:
    """Persist settings using the application database"""

    def __init__(self) -> None:
        self.db_manager = DatabaseManager(get_database_config())
        self._ensure_table()

    # ------------------------------------------------------------------
    def _ensure_table(self) -> None:
        conn = self.db_manager.get_connection()
        conn.execute_command(
            "CREATE TABLE IF NOT EXISTS app_settings (key TEXT PRIMARY KEY, value TEXT)"
        )

    # ------------------------------------------------------------------
    def save_settings(self, key: str, data: Dict[str, Any]) -> None:
        conn = self.db_manager.get_connection()
        conn.execute_command(
            "INSERT OR REPLACE INTO app_settings (key, value) VALUES (?, ?)",
            (key, json.dumps(data)),
        )

    # ------------------------------------------------------------------
    def load_settings(self, key: str) -> Dict[str, Any]:
        conn = self.db_manager.get_connection()
        rows = conn.execute_query(
            "SELECT value FROM app_settings WHERE key = ?", (key,)
        )
        if rows:
            try:
                return json.loads(rows[0]["value"])
            except Exception:
                return {}
        return {}


class SettingsManager:
    """High level manager for user and admin settings"""

    def __init__(self, persistence: Optional[SettingsPersistenceService] = None) -> None:
        self._persistence = persistence or SettingsPersistenceService()
        self._user_settings = UserSettings()
        self._admin_settings = AdminSettings()
        self.load_user_settings()
        self.load_admin_settings()

    # ------------------------------------------------------------------
    def save_user_settings(self, settings: UserSettings) -> None:
        self._user_settings = settings
        self._persistence.save_settings("user", asdict(settings))

    def load_user_settings(self) -> UserSettings:
        data = self._persistence.load_settings("user")
        if data:
            self._user_settings = UserSettings(**data)
        return self._user_settings

    # ------------------------------------------------------------------
    def save_admin_settings(self, settings: AdminSettings) -> None:
        self._admin_settings = settings
        self._persistence.save_settings("admin", asdict(settings))

    def load_admin_settings(self) -> AdminSettings:
        data = self._persistence.load_settings("admin")
        if data:
            self._admin_settings = AdminSettings(**data)
        return self._admin_settings


# Global instance
settings_manager = SettingsManager()

__all__ = [
    "UserSettings",
    "AdminSettings",
    "SettingsPersistenceService",
    "SettingsManager",
    "settings_manager",
]
