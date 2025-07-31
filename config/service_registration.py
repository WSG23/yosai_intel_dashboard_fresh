"""Service registration for dependency injection container."""

from core.service_container import ServiceContainer
from yosai_intel_dashboard.src.services.upload.protocols import (
    DeviceLearningServiceProtocol,
    FileProcessorProtocol,
    UploadControllerProtocol,
    UploadDataServiceProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)


def register_upload_services(container: ServiceContainer) -> None:
    """Register upload-related services with the container."""

    from config.dynamic_config import dynamic_config
    from yosai_intel_dashboard.src.services.configuration_service import DynamicConfigurationService
    from yosai_intel_dashboard.src.services.data_processing.async_file_processor import AsyncFileProcessor
    from yosai_intel_dashboard.src.services.device_learning_service import DeviceLearningService
    from yosai_intel_dashboard.src.services.door_mapping_service import DoorMappingService
    from yosai_intel_dashboard.src.services.interfaces import DoorMappingServiceProtocol
    from yosai_intel_dashboard.src.services.upload.processor import UploadProcessingService
    from yosai_intel_dashboard.src.services.upload.validator import ClientSideValidator
    from yosai_intel_dashboard.src.services.uploader import Uploader
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

    from yosai_intel_dashboard.src.services.upload_data_service import UploadDataService

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
