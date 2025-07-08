"""Service registration for dependency injection container."""
from core.enhanced_container import ServiceContainer
from services.upload.protocols import (
    UploadProcessingServiceProtocol,
    UploadValidatorProtocol,
    FileProcessorProtocol,
    UploadControllerProtocol,
    UploadStorageProtocol,
)


def register_upload_services(container: ServiceContainer) -> None:
    """Register upload-related services with the container."""

    from services.upload.core.processor import UploadProcessingService
    from services.upload.core.validator import ClientSideValidator
    from services.data_processing.async_file_processor import AsyncFileProcessor
    from utils.upload_store import UploadedDataStore

    upload_store = UploadedDataStore()
    container.register_singleton("upload_storage", upload_store)

    upload_validator = ClientSideValidator()
    container.register_singleton("upload_validator", upload_validator)

    file_processor = AsyncFileProcessor()
    container.register_singleton("file_processor", file_processor)

    upload_processor = UploadProcessingService(
        store=upload_store,
        processor=file_processor,
        validator=upload_validator,
    )
    container.register_singleton("upload_processor", upload_processor)

