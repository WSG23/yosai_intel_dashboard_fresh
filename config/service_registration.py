"""Service registration for dependency injection container."""

from core.service_container import ServiceContainer
from services.upload.protocols import (
    DeviceLearningServiceProtocol,
    FileProcessorProtocol,
    UploadControllerProtocol,
    UploadDataServiceProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)
from services.upload.controllers.upload_controller import UnifiedUploadController


def register_upload_services(container: ServiceContainer) -> None:
    """Register upload-related services with the container."""

    from config.dynamic_config import dynamic_config
    from services.configuration_service import DynamicConfigurationService
    from services.data_processing.async_file_processor import AsyncFileProcessor
    from services.device_learning_service import DeviceLearningService
    from services.door_mapping_service import DoorMappingService
    from services.interfaces import DoorMappingServiceProtocol
    from services.upload.processor import UploadProcessingService
    from services.upload.validator import ClientSideValidator
    from services.uploader import Uploader
    from utils.upload_store import UploadedDataStore

    upload_store = UploadedDataStore(dynamic_config.upload.folder)
    container.register_singleton("uploader", Uploader(upload_store))
    door_mapping_service = DoorMappingService(DynamicConfigurationService())
    container.register_singleton(
        "door_mapping_service",
        door_mapping_service,
        protocol=DoorMappingServiceProtocol,
    )
    container.register_singleton(
        "upload_storage", upload_store, protocol=UploadStorageProtocol
    )

    from services.upload_data_service import UploadDataService

    data_service = UploadDataService(upload_store)
    container.register_singleton(
        "upload_data_service",
        data_service,
        protocol=UploadDataServiceProtocol,
    )

    learning_service = DeviceLearningService()
    container.register_singleton(
        "device_learning_service",
        learning_service,
        protocol=DeviceLearningServiceProtocol,
    )

    upload_validator = ClientSideValidator()
    container.register_singleton(
        "upload_validator", upload_validator, protocol=UploadValidatorProtocol
    )

    file_processor = AsyncFileProcessor()
    container.register_singleton(
        "file_processor", file_processor, protocol=FileProcessorProtocol
    )

    upload_processor = UploadProcessingService(
        store=upload_store,
        learning_service=learning_service,
        processor=file_processor,
        validator=upload_validator,
    )
    container.register_singleton(
        "upload_processor",
        upload_processor,
        protocol=UploadProcessingServiceProtocol,
    )

    container.register_transient(
        "upload_controller",
        UnifiedUploadController,
        protocol=UploadControllerProtocol,
    )
