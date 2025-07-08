"""Service registration with proper DI patterns."""
from core.service_container import ServiceContainer
from services.upload.protocols import (
    UploadProcessingServiceProtocol,
    UploadValidatorProtocol,
    FileProcessorProtocol,
    UploadControllerProtocol,
    UploadStorageProtocol,
)


def register_upload_services(container: ServiceContainer) -> None:
    """Register upload services using factory pattern - NO direct instantiation."""

    # Register with factory functions for proper DI
    container.register_singleton(
        "upload_storage",
        _create_upload_store,
        protocol=UploadStorageProtocol,
    )

    container.register_singleton(
        "upload_validator",
        _create_validator,
        protocol=UploadValidatorProtocol,
    )

    container.register_singleton(
        "file_processor",
        _create_file_processor,
        protocol=FileProcessorProtocol,
    )

    container.register_singleton(
        "upload_processor",
        _create_upload_processor,
        protocol=UploadProcessingServiceProtocol,
    )

    container.register_transient(
        "upload_controller",
        _create_upload_controller,
        protocol=UploadControllerProtocol,
    )


def _create_upload_store(container: ServiceContainer):
    """Factory for upload storage with Unicode safety."""
    from utils.upload_store import UploadedDataStore
    return UploadedDataStore()


def _create_validator(container: ServiceContainer):
    """Factory for upload validator."""
    from services.upload.core.validator import ClientSideValidator
    return ClientSideValidator()


def _create_file_processor(container: ServiceContainer):
    """Factory for file processor with Unicode handling."""
    from services.data_processing.async_file_processor import AsyncFileProcessor
    return AsyncFileProcessor()


def _create_upload_processor(container: ServiceContainer):
    """Factory for upload processor with DI dependencies."""
    from services.upload.core.processor import UploadProcessingService

    store = container.get("upload_storage")
    processor = container.get("file_processor")
    validator = container.get("upload_validator")

    return UploadProcessingService(
        store=store,
        processor=processor,
        validator=validator,
    )


def _create_upload_controller(container: ServiceContainer):
    """Factory for upload controller with DI."""
    from services.upload.controllers.upload_controller import UnifiedUploadController

    upload_processor = container.get("upload_processor")
    return UnifiedUploadController(upload_processor)
