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
from services.metadata_enhancement_engine import register_metadata_services


def register_all_application_services(container: ServiceContainer) -> None:
    """Register all application services with the container."""

    register_core_infrastructure(container)
    register_analytics_services(container)
    register_learning_services(container)
    register_metadata_services(container)
    register_security_services(container)
    register_export_services(container)
    from services.upload.service_registration import register_upload_services

    register_upload_services(container)


def register_all_services(container: ServiceContainer) -> None:
    """Backward compatible alias for register_all_application_services."""
    register_all_application_services(container)


def register_core_infrastructure(container: ServiceContainer) -> None:
    from config import (
        ConfigLoader,
        ConfigManager,
        ConfigTransformer,
        ConfigValidator,
        create_config_manager,
    )
    from config.database_manager import DatabaseManager, DatabaseSettings
    from core.logging import LoggingService
    from services.configuration_service import (
        ConfigurationServiceProtocol,
        DynamicConfigurationService,
    )

    container.register_singleton("config_loader", ConfigLoader)
    container.register_singleton("config_validator", ConfigValidator)
    container.register_singleton("config_transformer", ConfigTransformer)
    container.register_singleton(
        "config_manager",
        ConfigManager,
        protocol=ConfigurationProtocol,
        factory=lambda c: create_config_manager(container=c),
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
        factory=lambda c: DatabaseManager(DatabaseSettings()),
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

    from config.cache_manager import get_cache_manager

    container.register_singleton(
        "cache_manager",
        get_cache_manager(),
    )


def register_analytics_services(container: ServiceContainer) -> None:
    """Register analytics components and service."""
    from core.protocols import AnalyticsServiceProtocol
    from services.analytics.protocols import (
        DataLoadingProtocol,
        DataProcessorProtocol,
        ReportGeneratorProtocol,
        PublishingProtocol,
    )
    from services.analytics_service import create_analytics_service
    from services.data_loading_service import DataLoadingService
    from services.data_processing_service import DataProcessingService
    from services.report_generation_service import ReportGenerationService
    from services.publishing_service import PublishingService
    from services.controllers.upload_controller import UnifiedUploadController
    from services.data_processing.processor import Processor
    from validation.security_validator import SecurityValidator

    container.register_singleton(
        "data_processing_service",
        DataProcessingService,
        protocol=DataProcessorProtocol,
        factory=lambda c: DataProcessingService(),
    )
    container.register_singleton(
        "upload_controller",
        UnifiedUploadController,
    )
    container.register_singleton(
        "data_loader",
        DataLoadingService,
        protocol=DataLoadingProtocol,
        factory=lambda c: DataLoadingService(
            c.get("upload_controller"),
            Processor(validator=SecurityValidator()),
        ),
    )
    container.register_singleton(
        "report_generator",
        ReportGenerationService,
        protocol=ReportGeneratorProtocol,
        factory=lambda c: ReportGenerationService(),
    )
    container.register_singleton(
        "publisher",
        PublishingService,
        protocol=PublishingProtocol,
        factory=lambda c: PublishingService(c.get("event_bus")),
    )
    container.register_singleton(
        "analytics_service",
        create_analytics_service(),
        protocol=AnalyticsServiceProtocol,
    )


def register_security_services(container: ServiceContainer) -> None:
    from validation.security_validator import SecurityValidator

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
