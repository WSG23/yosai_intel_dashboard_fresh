"""Comprehensive service registration for the DI container."""
from __future__ import annotations

from core.service_container import ServiceContainer
from services.upload.service_registration import register_upload_services
from core.protocols import (
    ConfigurationProtocol,
    DatabaseProtocol,
    LoggingProtocol,
    EventBusProtocol,
    StorageProtocol,
    SecurityServiceProtocol,
)
from services.analytics.protocols import (
    AnalyticsServiceProtocol,
    DataProcessorProtocol,
    ReportGeneratorProtocol,
    MetricsCalculatorProtocol,
)


def register_all_application_services(container: ServiceContainer) -> None:
    """Register all application services with the container."""

    register_core_infrastructure(container)
    register_analytics_services(container)
    register_security_services(container)
    register_export_services(container)
    register_upload_services(container)
    register_ui_service_factories(container)


def register_all_services(container: ServiceContainer) -> None:
    """Backward compatible alias for register_all_application_services."""
    register_all_application_services(container)


def register_core_infrastructure(container: ServiceContainer) -> None:
    from config.config import ConfigManager
    from core.logging_config import LoggingService
    from core.database import DatabaseManager

    container.register_singleton(
        "config_manager",
        ConfigManager,
        protocol=ConfigurationProtocol,
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
    )

    from core.events import EventBus
    container.register_singleton(
        "event_bus",
        EventBus,
        protocol=EventBusProtocol,
    )


def register_analytics_services(container: ServiceContainer) -> None:
    from services.analytics_service import AnalyticsService
    from services.analytics.data_processor import DataProcessor
    from services.analytics.report_generator import ReportGenerator
    from services.analytics.metrics_calculator import MetricsCalculator

    container.register_singleton(
        "analytics_service",
        AnalyticsService,
        protocol=AnalyticsServiceProtocol,
        factory=lambda c: AnalyticsService(
            database=c.get("database_manager", DatabaseProtocol),
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
    from services.export_service import ExportService
    from core.protocols import ExportServiceProtocol

    container.register_transient(
        "export_service",
        ExportService,
        protocol=ExportServiceProtocol,
    )


def register_ui_service_factories(container: ServiceContainer) -> None:
    from pages.factories import AnalyticsPageFactory

    container.register_transient(
        "analytics_page_factory", AnalyticsPageFactory

    )
