"""Service registration for upload domain using ``ServiceContainer``."""

from __future__ import annotations

from utils.upload_store import UploadedDataStore
from yosai_intel_dashboard.src.core.service_container import (
    CircularDependencyError,
    DependencyInjectionError,
    ServiceContainer,
    ServiceLifetime,
)
from config.dynamic_config import (
    dynamic_config,
)
from yosai_intel_dashboard.src.services.async_file_processor import AsyncFileProcessor
from yosai_intel_dashboard.src.services.device_learning_service import (
    DeviceLearningService,
)
from yosai_intel_dashboard.src.services.interfaces import (
    DeviceLearningServiceProtocol,
    UploadDataServiceProtocol,
)
from yosai_intel_dashboard.src.services.upload.controllers.upload_controller import (
    UnifiedUploadController,
)
from yosai_intel_dashboard.src.services.upload.core.processor import (
    UploadProcessingService,
)
from yosai_intel_dashboard.src.services.upload.core.validator import ClientSideValidator
from yosai_intel_dashboard.src.services.upload.protocols import (
    FileProcessorProtocol,
    UploadControllerProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)
from yosai_intel_dashboard.src.services.upload_data_service import UploadDataService


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
