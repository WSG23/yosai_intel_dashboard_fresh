"""Upload Domain Public API

This module exposes the main interfaces for the upload domain.
Other packages should import from here rather than submodules.
"""

from core.unicode import safe_encode_text
from unicode_toolkit import decode_upload_content
from utils.upload_store import UploadedDataStore as UploadStorage

from .ai import AISuggestionService, analyze_device_name_with_ai
from .controllers.upload_controller import UnifiedUploadController as UploadController
from .core.processor import UploadProcessingService
from .core.validator import ClientSideValidator as UploadValidator
from .helpers import save_ai_training_data
from .protocols import (
    DeviceLearningServiceProtocol,
    FileProcessorProtocol,
    UploadControllerProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
    get_device_learning_service,
)

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
    "AISuggestionService",
    "analyze_device_name_with_ai",
    "save_ai_training_data",
]

DOMAIN_NAME = "upload"
DOMAIN_VERSION = "1.0.0"
