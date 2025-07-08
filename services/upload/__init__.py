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
)

from .core.processor import UploadProcessingService
from .core.validator import ClientSideValidator as UploadValidator
from utils.upload_store import UploadedDataStore as UploadStorage
from .controllers.upload_controller import UnifiedUploadController as UploadController
from .utils.file_parser import FileParser
from .utils.unicode_handler import safe_unicode_encode, decode_upload_content

__all__ = [
    "UploadProcessingServiceProtocol",
    "UploadValidatorProtocol",
    "FileProcessorProtocol",
    "UploadStorageProtocol",
    "UploadControllerProtocol",
    "UploadProcessingService",
    "UploadValidator",
    "UploadStorage",
    "UploadController",
    "FileParser",
    "safe_unicode_encode",
    "decode_upload_content",
]

DOMAIN_NAME = "upload"
DOMAIN_VERSION = "1.0.0"
