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
    try:
        from services.analytics.data_processor import DataProcessor
        from services.analytics.metrics_calculator import MetricsCalculator
        from services.analytics.protocols import (
            AnalyticsServiceProtocol,
            DataProcessorProtocol,
            MetricsCalculatorProtocol,
            ReportGeneratorProtocol,
        )
        from services.analytics.report_generator import ReportGenerator
        from services.analytics_service import AnalyticsService
    except Exception as exc:  # pragma: no cover - optional dependency
        logging.warning(f"Analytics services unavailable: {exc}")
        return

    container.register_singleton(
        "analytics_service",
        AnalyticsService,
        protocol=AnalyticsServiceProtocol,
        factory=lambda c: AnalyticsService(
            database=c.get("database_manager"),
            data_processor=c.get("data_processor", DataProcessorProtocol),
            config=c.get("config_manager", ConfigurationProtocol),
            event_bus=c.get("event_bus", EventBusProtocol),
            storage=c.get("file_storage", StorageProtocol),
        ),
    )

    container.register_singleton(
        "data_processor",
        DataProcessor,
        protocol=DataProcessorProtocol,
        factory=lambda c: DataProcessor(),
    )

    container.register_transient(
        "report_generator",
        ReportGenerator,
        protocol=ReportGeneratorProtocol,
    )

    container.register_singleton(
        "metrics_calculator",
        MetricsCalculator,
        protocol=MetricsCalculatorProtocol,
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
