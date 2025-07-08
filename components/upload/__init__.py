"""Upload UI Components Public API."""
from .validators.client_validator import ClientSideValidator
from .ui.upload_area import UploadArea
from .unified_upload_component import UnifiedUploadComponent

__all__ = [
    "UploadArea",
    "ClientSideValidator",
    "UnifiedUploadComponent",
]

COMPONENT_LIBRARY_VERSION = "1.0.0"
SUPPORTED_THEMES = ["light", "dark", "high-contrast"]
