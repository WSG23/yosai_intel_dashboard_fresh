"""Comprehensive service registration for the DI container."""
from __future__ import annotations

from core.service_container import ServiceContainer
from services.upload.service_registration import register_upload_services


def register_all_application_services(container: ServiceContainer) -> None:
    """Register all application services with the container."""

    register_core_infrastructure(container)
    register_analytics_services(container)
    register_security_services(container)
    register_export_services(container)
    register_upload_services(container)
    register_ui_service_factories(container)


def register_core_infrastructure(container: ServiceContainer) -> None:
    from config.config import ConfigManager
    from core.logging_config import LoggingService
    from core.database import DatabaseManager

    container.register_singleton(
        "config_manager", ConfigManager
    )
    container.register_singleton(
        "logging_service", LoggingService
    )
    container.register_singleton(
        "database_manager", DatabaseManager
    )


def register_analytics_services(container: ServiceContainer) -> None:
    from services.analytics_service import AnalyticsService

    container.register_singleton(
        "analytics_service", AnalyticsService
    )


def register_security_services(container: ServiceContainer) -> None:
    from security.validation_service import SecurityValidator

    container.register_singleton(
        "security_validator", SecurityValidator
    )


def register_export_services(container: ServiceContainer) -> None:
    from services.export_service import ExportService

    container.register_transient(
        "export_service", ExportService
    )


def register_ui_service_factories(container: ServiceContainer) -> None:
    from pages.factories import AnalyticsPageFactory

    container.register_transient(
        "analytics_page_factory", AnalyticsPageFactory
    )
