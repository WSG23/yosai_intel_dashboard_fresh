"""Performance settings ORM model and manager."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.orm import declarative_base

from yosai_intel_dashboard.src.core.plugins.config.cache_manager import (
    MemoryCacheManager,
)
from yosai_intel_dashboard.src.core.plugins.config.interfaces import (
    ICacheManager,
    IDatabaseManager,
)
from yosai_intel_dashboard.src.database.secure_exec import execute_query

logger = logging.getLogger(__name__)

Base = declarative_base()


class PerformanceSetting(Base):
    """SQLAlchemy ORM model for the ``performance_settings`` table."""

    __tablename__ = "performance_settings"

    id = Column(Integer, primary_key=True)
    setting_name = Column(String(128), unique=True, nullable=False)
    value = Column(String(256), nullable=False)
    type = Column(String(32), nullable=False, default="string")
    description = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "setting_name": self.setting_name,
            "value": self.value,
            "type": self.type,
            "description": self.description,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS performance_settings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    setting_name TEXT UNIQUE NOT NULL,
    value TEXT NOT NULL,
    type TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
"""


class PerformanceSettingsManager:
    """Manager for loading and updating ``PerformanceSetting`` records."""

    _CACHE_KEY = "performance_settings_all"

    def __init__(
        self,
        database_manager: IDatabaseManager,
        cache_manager: ICacheManager | None = None,
        cache_ttl: int = 300,
    ) -> None:
        self.db = database_manager
        self.cache = cache_manager or MemoryCacheManager(
            cache_config={"timeout_seconds": cache_ttl}
        )
        self.cache_ttl = cache_ttl
        self._ensure_schema()

    # ------------------------------------------------------------------
    def _ensure_schema(self) -> None:
        """Create table if it does not exist."""
        try:
            execute_query(self.db, CREATE_TABLE_SQL)
        except Exception as exc:  # pragma: no cover - best effort
            logger.error("Failed to ensure performance_settings schema: %s", exc)

    # ------------------------------------------------------------------
    def load_settings(self, force_refresh: bool = False) -> List[PerformanceSetting]:
        """Load all settings with caching."""
        if not force_refresh:
            cached = self.cache.get(self._CACHE_KEY)
            if cached is not None:
                return cached

        rows = execute_query(
            self.db,
            "SELECT id, setting_name, value, type, description, updated_at FROM performance_settings",
        )
        settings = [self._row_to_model(row) for row in rows]
        self.cache.set(self._CACHE_KEY, settings, ttl=self.cache_ttl)
        return settings

    # ------------------------------------------------------------------
    def get_setting(self, name: str) -> PerformanceSetting | None:
        """Return a single setting by name."""
        settings = self.load_settings()
        for item in settings:
            if item.setting_name == name:
                return item
        return None

    # ------------------------------------------------------------------
    def update_setting(
        self,
        name: str,
        value: Any,
        *,
        type: str | None = None,
        description: str | None = None,
    ) -> PerformanceSetting:
        """Create or update a setting with validation and cache refresh."""
        self._validate(name, value, type)
        current = self.get_setting(name)
        now = datetime.utcnow()

        if current is None:
            execute_query(
                self.db,
                """
                INSERT INTO performance_settings (setting_name, value, type, description, updated_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (name, str(value), type or self._infer_type(value), description, now),
            )
        else:
            execute_query(
                self.db,
                """
                UPDATE performance_settings
                SET value = ?, type = ?, description = ?, updated_at = ?
                WHERE setting_name = ?
                """,
                (str(value), type or current.type, description, now, name),
            )

        self.cache.delete(self._CACHE_KEY)
        return self.get_setting(name) or PerformanceSetting(
            id=-1,
            setting_name=name,
            value=str(value),
            type=type or self._infer_type(value),
        )

    # ------------------------------------------------------------------
    def _validate(self, name: str, value: Any, type_name: str | None) -> None:
        if not name or len(name) > 128:
            raise ValueError("setting_name must be between 1 and 128 characters")
        if type_name is not None and type_name not in {
            "int",
            "float",
            "str",
            "bool",
            "json",
            "string",
        }:
            raise ValueError(f"Unsupported type: {type_name}")
        # Basic cast check
        if type_name:
            self._cast_value(value, type_name)

    # ------------------------------------------------------------------
    def _cast_value(self, value: Any, type_name: str) -> Any:
        if type_name in {"str", "string"}:
            return str(value)
        if type_name == "int":
            return int(value)
        if type_name == "float":
            return float(value)
        if type_name == "bool":
            if isinstance(value, str):
                return value.lower() in {"1", "true", "yes"}
            return bool(value)
        if type_name == "json":
            import json

            if isinstance(value, str):
                json.loads(value)
            else:
                json.dumps(value)
            return value
        raise ValueError(f"Unsupported type: {type_name}")

    # ------------------------------------------------------------------
    def _infer_type(self, value: Any) -> str:
        if isinstance(value, bool):
            return "bool"
        if isinstance(value, int):
            return "int"
        if isinstance(value, float):
            return "float"
        if isinstance(value, (dict, list)):
            return "json"
        return "string"

    # ------------------------------------------------------------------
    @staticmethod
    def _row_to_model(row: Dict[str, Any]) -> PerformanceSetting:
        return PerformanceSetting(
            id=row.get("id"),
            setting_name=row.get("setting_name"),
            value=row.get("value"),
            type=row.get("type"),
            description=row.get("description"),
            updated_at=row.get("updated_at"),
        )


__all__ = ["PerformanceSetting", "PerformanceSettingsManager", "CREATE_TABLE_SQL"]
