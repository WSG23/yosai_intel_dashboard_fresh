"""Service registration for upload domain using ``ServiceContainer``."""

from __future__ import annotations

from config.dynamic_config import dynamic_config
from core.protocols import FileProcessorProtocol
from core.service_container import (
    CircularDependencyError,
    DependencyInjectionError,
    ServiceContainer,
    ServiceLifetime,
)
from yosai_intel_dashboard.src.services.async_file_processor import AsyncFileProcessor
from yosai_intel_dashboard.src.services.device_learning_service import DeviceLearningService
from yosai_intel_dashboard.src.services.interfaces import (
    DeviceLearningServiceProtocol,
    UploadDataServiceProtocol,
)
from yosai_intel_dashboard.src.services.upload.controllers.upload_controller import UnifiedUploadController
from yosai_intel_dashboard.src.services.upload.file_processor_service import FileProcessor
from yosai_intel_dashboard.src.services.upload.learning_coordinator import LearningCoordinator
from yosai_intel_dashboard.src.services.upload.processor import UploadProcessingService
from components.ui_builder import UploadUIBuilder
from yosai_intel_dashboard.src.services.upload.validator import ClientSideValidator
from yosai_intel_dashboard.src.services.upload.protocols import (
    UploadControllerProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)
from yosai_intel_dashboard.src.services.upload_data_service import UploadDataService
from utils.upload_store import UploadedDataStore
from validation.file_validator import FileValidator


def register_upload_services(container: ServiceContainer) -> None:
    """Register upload related services with the container."""

    upload_store = UploadedDataStore(dynamic_config.upload.folder)
    container.register_singleton(
        "upload_storage",
        upload_store,
        protocol=UploadStorageProtocol,
    )

    container.register_singleton(
        "upload_data_service",
        UploadDataService(upload_store),
        protocol=UploadDataServiceProtocol,
    )

    container.register_singleton(
        "device_learning_service",
        DeviceLearningService,
        protocol=DeviceLearningServiceProtocol,
    )

    container.register_singleton(
        "file_processor",
        AsyncFileProcessor,
        protocol=FileProcessorProtocol,
    )

    container.register_singleton(
        "upload_validator",
        ClientSideValidator,
        protocol=UploadValidatorProtocol,
    )

    container.register_singleton(
        "file_validator",
        FileValidator,
    )

    container.register_singleton(
        "file_processor_service",
        FileProcessor,
    )

    container.register_singleton(
        "learning_coordinator",
        LearningCoordinator,
    )

    container.register_singleton(
        "ui_builder",
        UploadUIBuilder,
    )

    container.register_singleton(
        "upload_processor",
        UploadProcessingService,
        protocol=UploadProcessingServiceProtocol,
    )

    container.register_transient(
        "upload_controller",
        UnifiedUploadController,
        protocol=UploadControllerProtocol,
    )

    container.register_health_check("upload_storage", lambda s: True)


def configure_upload_dependencies(container: ServiceContainer) -> None:
    """Convenience wrapper for registration with validation."""

    register_upload_services(container)
    results = container.validate_registrations()
    if results["missing_dependencies"]:
        raise DependencyInjectionError(
            f"Missing dependencies: {results['missing_dependencies']}"
        )
    if results["circular_dependencies"]:
        raise CircularDependencyError(
            f"Circular dependencies: {results['circular_dependencies']}"
        )
