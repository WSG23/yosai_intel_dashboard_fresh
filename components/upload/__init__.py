"""Upload UI Components Public API."""
from .validators.client_validator import ClientSideValidator
from .ui.upload_area import UploadArea

__all__ = [
    "UploadArea",
    "ClientSideValidator",
]

COMPONENT_LIBRARY_VERSION = "1.0.0"
SUPPORTED_THEMES = ["light", "dark", "high-contrast"]
