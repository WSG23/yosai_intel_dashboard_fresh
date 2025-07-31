import inspect

from core.protocols import FileProcessorProtocol
from services.data_processing.async_file_processor import AsyncFileProcessor
from services.upload.processor import UploadProcessingService
from services.upload.protocols import (
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
)
from services.upload.validator import ClientSideValidator
from yosai_intel_dashboard.src.utils.upload_store import UploadedDataStore


def test_processing_service_implements_protocol() -> None:
    assert issubclass(UploadProcessingService, UploadProcessingServiceProtocol)


def test_validator_implements_protocol() -> None:
    assert issubclass(ClientSideValidator, UploadValidatorProtocol)


def test_file_processor_implements_protocol() -> None:
    assert issubclass(AsyncFileProcessor, FileProcessorProtocol)


def test_storage_implements_protocol() -> None:
    assert issubclass(UploadedDataStore, UploadStorageProtocol)
