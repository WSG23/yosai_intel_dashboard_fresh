import inspect

from services.upload.core.processor import UploadProcessingService
from services.upload.core.validator import ClientSideValidator
from services.data_processing.async_file_processor import AsyncFileProcessor
from utils.upload_store import UploadedDataStore
from services.upload.protocols import (
    UploadProcessingServiceProtocol,
    UploadValidatorProtocol,
    FileProcessorProtocol,
    UploadStorageProtocol,
)


def test_processing_service_implements_protocol() -> None:
    assert issubclass(UploadProcessingService, UploadProcessingServiceProtocol)


def test_validator_implements_protocol() -> None:
    assert issubclass(ClientSideValidator, UploadValidatorProtocol)


def test_file_processor_implements_protocol() -> None:
    assert issubclass(AsyncFileProcessor, FileProcessorProtocol)


def test_storage_implements_protocol() -> None:
    assert issubclass(UploadedDataStore, UploadStorageProtocol)
