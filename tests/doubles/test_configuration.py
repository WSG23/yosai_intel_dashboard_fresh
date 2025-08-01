from __future__ import annotations

from typing import Any, Dict

from yosai_intel_dashboard.src.core.protocols import ConfigurationProtocol


class TestConfiguration(ConfigurationProtocol):
    """Simple configuration object for tests."""

    def __init__(self) -> None:
        self.database: Dict[str, Any] = {}
        self.app: Dict[str, Any] = {}
        self.security: Dict[str, Any] = {}
        self.upload: Dict[str, Any] = {}

    def get_database_config(self) -> Dict[str, Any]:
        return self.database

    def get_app_config(self) -> Dict[str, Any]:
        return self.app

    def get_security_config(self) -> Dict[str, Any]:
        return self.security

    def get_upload_config(self) -> Dict[str, Any]:
        return self.upload

    def reload_config(self) -> None:
        pass

    def validate_config(self) -> Dict[str, Any]:
        return {"valid": True}
