"""Comprehensive service registration for the DI container."""

from __future__ import annotations

import logging

from core.protocols import (
    ConfigurationProtocol,
    DatabaseProtocol,
    EventBusProtocol,
    LoggingProtocol,
    SecurityServiceProtocol,
    StorageProtocol,
)
from core.service_container import ServiceContainer


def register_all_application_services(container: ServiceContainer) -> None:
    """Register all application services with the container."""

    register_core_infrastructure(container)
    register_analytics_services(container)
    register_learning_services(container)
    register_security_services(container)
    register_export_services(container)
    from services.upload.service_registration import register_upload_services

    register_upload_services(container)


def register_all_services(container: ServiceContainer) -> None:
    """Backward compatible alias for register_all_application_services."""
    register_all_application_services(container)


def register_core_infrastructure(container: ServiceContainer) -> None:
    from config.config import ConfigManager
    from config.database_manager import DatabaseConfig, DatabaseManager
    from core.logging import LoggingService
    from services.configuration_service import (
        ConfigurationServiceProtocol,
        DynamicConfigurationService,
    )

    container.register_singleton(
        "config_manager",
        ConfigManager,
        protocol=ConfigurationProtocol,
    )
    container.register_singleton(
        "configuration_service",
        DynamicConfigurationService,
        protocol=ConfigurationServiceProtocol,
    )
    container.register_singleton(
        "logging_service",
        LoggingService,
        protocol=LoggingProtocol,
    )
    container.register_singleton(
        "database_manager",
        DatabaseManager,
        protocol=DatabaseProtocol,
        factory=lambda c: DatabaseManager(DatabaseConfig()),
    )

    from core.events import EventBus

    container.register_singleton(
        "event_bus",
        EventBus,
        protocol=EventBusProtocol,
    )

    # Register generic file storage service for analytics
    from core.storage.file_storage import FileStorageService

    container.register_singleton(
        "file_storage",
        FileStorageService,
        protocol=StorageProtocol,
    )


def register_analytics_services(container: ServiceContainer) -> None:
    class SimpleAnalyticsService:
        def get_dashboard_summary(self, time_range: str = "30d") -> Dict[str, Any]:
            return {"status": "stub", "message": "Analytics not configured"}

        def analyze_access_patterns(self, days: int, user_id: str | None = None) -> Dict[str, Any]:
            return {"status": "stub"}

        def detect_anomalies(self, data, sensitivity: float = 0.5):
            return []

        def generate_report(self, report_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
            return {"status": "stub"}

        def get_user_activity_summary(self, user_id: str, days: int = 30) -> Dict[str, Any]:
            return {"status": "stub"}

        def get_facility_statistics(self, facility_id: str | None = None) -> Dict[str, Any]:
            return {"status": "stub"}

        def health_check(self) -> Dict[str, Any]:
            return {"status": "healthy", "service": "analytics_stub"}

    container.register_singleton(
        "analytics_service",
        SimpleAnalyticsService(),
    )


def register_security_services(container: ServiceContainer) -> None:
    from core.security_validator import SecurityValidator

    container.register_singleton(
        "security_validator",
        SecurityValidator,
        protocol=SecurityServiceProtocol,
    )


def register_export_services(container: ServiceContainer) -> None:
    from core.protocols import ExportServiceProtocol
    from services.export_service import ExportService

    container.register_transient(
        "export_service",
        ExportService,
        protocol=ExportServiceProtocol,
    )


def register_learning_services(container: ServiceContainer) -> None:
    """Register device learning service with the container."""

    from services.device_learning_service import create_device_learning_service

    container.register_singleton(
        "device_learning_service",
        create_device_learning_service(),
    )
