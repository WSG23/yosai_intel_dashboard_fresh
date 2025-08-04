"""Comprehensive service registration for the DI container."""

from __future__ import annotations


from yosai_intel_dashboard.src.core.interfaces.protocols import (
    ConfigurationProtocol,
    EventBusProtocol,
    LoggingProtocol,
    SecurityServiceProtocol,
    StorageProtocol,
)
from yosai_intel_dashboard.src.infrastructure.di.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.metadata_enhancement_engine import register_metadata_services
import warnings


def register_all_application_services(container: ServiceContainer) -> None:
    """Register all application services with the container."""

    register_core_infrastructure(container)
    register_analytics_services(container)
    register_learning_services(container)
    register_metadata_services(container)
    register_security_services(container)
    register_export_services(container)
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
    from yosai_intel_dashboard.src.services.upload.service_registration import register_upload_services

    register_upload_services(container, config=dynamic_config)


def register_all_services(container: ServiceContainer) -> None:
    """Backward compatible alias for register_all_application_services."""
    warnings.warn(
        "register_all_services is deprecated; use register_all_application_services",
        DeprecationWarning,
        stacklevel=2,
    )
    register_all_application_services(container)


def register_core_infrastructure(container: ServiceContainer) -> None:
    from config import (
        ConfigLoader,
        ConfigManager,
        ConfigTransformer,
        ConfigValidator,
        create_config_manager,
    )
    from yosai_intel_dashboard.src.infrastructure.config.database_manager import (
        DatabaseConnectionFactory,
        DatabaseSettings,
    )
    from yosai_intel_dashboard.src.infrastructure.config.dynamic_config import dynamic_config
    from yosai_intel_dashboard.src.core.interfaces import ConfigProviderProtocol
    from yosai_intel_dashboard.src.core.logging import LoggingService
    from yosai_intel_dashboard.src.services.configuration_service import (
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
        "dynamic_config",
        dynamic_config,
        protocol=ConfigProviderProtocol,
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
    from yosai_intel_dashboard.src.error_handling import ErrorHandler
    container.register_singleton("error_handler", ErrorHandler)
    container.register_singleton(
        "database_connection_factory",
        DatabaseConnectionFactory,
        factory=lambda c: DatabaseConnectionFactory(DatabaseSettings()),
    )

    from yosai_intel_dashboard.src.core.events import EventBus

    container.register_singleton(
        "event_bus",
        EventBus,
        protocol=EventBusProtocol,
    )

    # Register generic file storage service for analytics
    from yosai_intel_dashboard.src.core.storage.file_storage import FileStorageService

    container.register_singleton(
        "file_storage",
        FileStorageService,
        protocol=StorageProtocol,
    )

    from yosai_intel_dashboard.src.infrastructure.config.cache_manager import get_cache_manager

    container.register_singleton(
        "cache_manager",
        get_cache_manager(),
    )


def register_analytics_services(container: ServiceContainer) -> None:
    """Register analytics components and service."""
    from yosai_intel_dashboard.src.core.interfaces.protocols import (
        AnalyticsServiceProtocol,
        ConfigProviderProtocol,
        EventBusProtocol,
        StorageProtocol,
    )
    from yosai_intel_dashboard.src.mapping.factories.service_factory import (
        create_mapping_service,
    )
    from yosai_intel_dashboard.src.services.analytics.calculator import create_calculator
    from yosai_intel_dashboard.src.services.analytics.protocols import (
        CalculatorProtocol,
        DataLoadingProtocol,
        DataProcessorProtocol,
        PublishingProtocol,
        ReportGeneratorProtocol,
        UploadAnalyticsProtocol,
    )
    from yosai_intel_dashboard.src.services.analytics.upload_analytics import UploadAnalyticsProcessor
    from yosai_intel_dashboard.src.services.analytics.analytics_service import AnalyticsService
    from yosai_intel_dashboard.src.services.controllers.upload_controller import UploadProcessingController
    from yosai_intel_dashboard.src.services.controllers.protocols import UploadProcessingControllerProtocol
    from yosai_intel_dashboard.src.services.data_loading_service import DataLoadingService
    from yosai_intel_dashboard.src.services.data_processing.processor import Processor
    from yosai_intel_dashboard.src.services.data_processing_service import DataProcessingService
    from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
        MappingServiceProtocol,
        UploadDataServiceProtocol,
        get_database_analytics_retriever,
    )
    from yosai_intel_dashboard.src.services.protocols.processor import ProcessorProtocol
    from yosai_intel_dashboard.src.services.publishing_service import PublishingService
    from yosai_intel_dashboard.src.services.report_generation_service import ReportGenerationService

    container.register_singleton(
        "data_processing_service",
        DataProcessingService,
        protocol=DataProcessorProtocol,
        factory=lambda c: DataProcessingService(),
    )
    container.register_singleton(
        "processor",
        Processor,
        protocol=ProcessorProtocol,
        factory=lambda c: Processor(
            validator=c.get("security_validator"),
            mapping_service=c.get("mapping_service", MappingServiceProtocol),
        ),
    )
    container.register_singleton(
        "upload_analytics_processor",
        UploadAnalyticsProcessor,
        protocol=UploadAnalyticsProtocol,
        factory=lambda c: UploadAnalyticsProcessor(
            c.get("security_validator"),
            c.get("processor", ProcessorProtocol),
        ),
    )
    container.register_singleton(
        "upload_processing_controller",
        UploadProcessingController,
        factory=lambda c: UploadProcessingController(
            c.get("security_validator"),
            c.get("processor", ProcessorProtocol),
            c.get("upload_data_service", UploadDataServiceProtocol),
            c.get("upload_analytics_processor", UploadAnalyticsProtocol),
        ),
    )
    container.register_singleton(
        "mapping_service",
        create_mapping_service(container=container),
        protocol=MappingServiceProtocol,
    )
    container.register_singleton(
        "data_loader",
        DataLoadingService,
        protocol=DataLoadingProtocol,
        factory=lambda c: DataLoadingService(
            c.get("upload_processing_controller"),
            c.get("processor", ProcessorProtocol),
        ),
    )
    container.register_singleton(
        "report_generator",
        ReportGenerationService,
        protocol=ReportGeneratorProtocol,
        factory=lambda c: ReportGenerationService(),
    )
    container.register_singleton(
        "calculator",
        create_calculator(),
        protocol=CalculatorProtocol,
    )
    container.register_singleton(
        "publisher",
        PublishingService,
        protocol=PublishingProtocol,
        factory=lambda c: PublishingService(c.get("event_bus")),
    )
    def _create_analytics_service(c):
        factory = c.get("database_connection_factory")
        db_conn = factory.create() if factory else None
        return AnalyticsService(
            database=db_conn,
            data_processor=c.get("data_processing_service", DataProcessorProtocol),
            config=c.get("dynamic_config", ConfigProviderProtocol),
            event_bus=c.get("event_bus", EventBusProtocol),
            storage=c.get("file_storage", StorageProtocol),
            upload_data_service=c.get("upload_data_service", UploadDataServiceProtocol),
            model_registry=None,
            loader=c.get("data_loader", DataLoadingProtocol),
            calculator=c.get("calculator", CalculatorProtocol),
            publisher=c.get("publisher", PublishingProtocol),
            report_generator=c.get("report_generator", ReportGeneratorProtocol),
            db_retriever=get_database_analytics_retriever(db_conn),
            upload_controller=c.get(
                "upload_processing_controller", UploadProcessingControllerProtocol
            ),
            upload_processor=c.get(
                "upload_analytics_processor", UploadAnalyticsProtocol
            ),
        )

    container.register_singleton(
        "analytics_service",
        AnalyticsService,
        protocol=AnalyticsServiceProtocol,
        factory=_create_analytics_service,
    )


def register_security_services(container: ServiceContainer) -> None:
    from validation.security_validator import SecurityValidator

    container.register_singleton(
        "security_validator",
        SecurityValidator,
        protocol=SecurityServiceProtocol,
    )


def register_export_services(container: ServiceContainer) -> None:
    from yosai_intel_dashboard.src.core.interfaces.protocols import ExportServiceProtocol
    from yosai_intel_dashboard.src.services.export_service import ExportService

    container.register_transient(
        "export_service",
        ExportService,
        protocol=ExportServiceProtocol,
    )


def register_learning_services(container: ServiceContainer) -> None:
    """Register device learning service with the container."""

    from yosai_intel_dashboard.src.services.device_learning_service import create_device_learning_service

    container.register_singleton(
        "device_learning_service",
        create_device_learning_service(),
    )
