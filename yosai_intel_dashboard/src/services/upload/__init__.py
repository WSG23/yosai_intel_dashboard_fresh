"""Upload Domain Public API.

This module exposes the main interfaces for the upload domain.
Historically importing this package pulled in a large dependency graph that
made simple helpers (like :mod:`upload_processing`) expensive to import.  To
keep lightweight scripts fast and test-friendly we only import the heavy
components when the ``LIGHTWEIGHT_SERVICES`` environment variable is **not**
set.
"""

import os

from yosai_intel_dashboard.src.core.interfaces.protocols import FileProcessorProtocol
from yosai_intel_dashboard.src.core.base_utils import safe_encode_text
from unicode_toolkit import decode_upload_content
from validation.security_validator import SecurityValidator

from .protocols import (
    DeviceLearningServiceProtocol,
    UploadControllerProtocol,
    UploadProcessingServiceProtocol,
    UploadStorageProtocol,
    UploadValidatorProtocol,
    get_device_learning_service,
)

if not os.getenv("LIGHTWEIGHT_SERVICES"):
    from .ai import AISuggestionService, analyze_device_name_with_ai
    from .controllers.upload_controller import (
        UnifiedUploadController as UploadController,
    )
    from .helpers import save_ai_training_data
    from .processor import UploadProcessingService
    from .upload_core import UploadCore
    from .upload_types import UploadResult, ValidationResult

    _extra_all = [
        "UploadProcessingService",
        "UploadController",
        "AISuggestionService",
        "analyze_device_name_with_ai",
        "save_ai_training_data",
        "UploadCore",
        "ValidationResult",
        "UploadResult",
    ]
else:  # pragma: no cover - lightweight mode
    _extra_all: list[str] = []

__all__ = [
    "UploadProcessingServiceProtocol",
    "UploadValidatorProtocol",
    "FileProcessorProtocol",
    "UploadStorageProtocol",
    "UploadControllerProtocol",
    "DeviceLearningServiceProtocol",
    "get_device_learning_service",
    "SecurityValidator",
    "safe_encode_text",
    "decode_upload_content",
] + _extra_all

DOMAIN_NAME = "upload"
DOMAIN_VERSION = "1.0.0"
