"""Upload Domain Public API

This module exposes the main interfaces for the upload domain.
Other packages should import from here rather than submodules.
"""

from .protocols import (
    UploadProcessingServiceProtocol,
    UploadValidatorProtocol,
    FileProcessorProtocol,
    UploadStorageProtocol,
    UploadControllerProtocol,
    DeviceLearningServiceProtocol,
    get_device_learning_service,
)

from .core.processor import UploadProcessingService
from .core.validator import ClientSideValidator as UploadValidator
from utils.upload_store import UploadedDataStore as UploadStorage
from .controllers.upload_controller import UnifiedUploadController as UploadController
from .utils.unicode_handler import decode_upload_content
from core.unicode import safe_encode_text

__all__ = [
    "UploadProcessingServiceProtocol",
    "UploadValidatorProtocol",
    "FileProcessorProtocol",
    "UploadStorageProtocol",
    "UploadControllerProtocol",
    "DeviceLearningServiceProtocol",
    "get_device_learning_service",
    "UploadProcessingService",
    "UploadValidator",
    "UploadStorage",
    "UploadController",
    "safe_encode_text",
    "decode_upload_content",
]

DOMAIN_NAME = "upload"
DOMAIN_VERSION = "1.0.0"
