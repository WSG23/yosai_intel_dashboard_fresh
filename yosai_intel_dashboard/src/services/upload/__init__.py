"""Upload Domain Public API

This module exposes the main interfaces for the upload domain.
Other packages should import from here rather than submodules.
"""

from core.protocols import FileProcessorProtocol
from core.unicode import safe_encode_text
from unicode_toolkit import decode_upload_content
from utils.upload_store import UploadedDataStore as UploadStorage
from validation.security_validator import SecurityValidator

from .ai import AISuggestionService, analyze_device_name_with_ai
from .controllers.upload_controller import UnifiedUploadController as UploadController
from .processor import UploadProcessingService
from .helpers import save_ai_training_data
from .upload_core import UploadCore
from .upload_types import ValidationResult, UploadResult
from .protocols import (
    DeviceLearningServiceProtocol,
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
    "SecurityValidator",
    "UploadStorage",
    "UploadController",
    "safe_encode_text",
    "decode_upload_content",
    "AISuggestionService",
    "analyze_device_name_with_ai",
    "save_ai_training_data",
    "UploadCore",
    "ValidationResult",
    "UploadResult",
]

DOMAIN_NAME = "upload"
DOMAIN_VERSION = "1.0.0"
