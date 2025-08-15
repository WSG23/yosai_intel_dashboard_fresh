"""Public API for working with uploaded data."""

from .upload.upload_data_service import (
    UploadDataService,
    clear_uploaded_data,
    get_file_info,
    get_uploaded_data,
    get_uploaded_filenames,
    load_dataframe,
    load_mapping,
    save_mapping,
)

__all__ = [
    "UploadDataService",
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "load_dataframe",
    "load_mapping",
    "save_mapping",
]

# ---- Protocol shim (safe at runtime) ----------------------------------------
# Some modules import `UploadDataServiceProtocol` for typing.
# If it's not defined here, provide a permissive, runtime-checkable Protocol
# so imports succeed and runtime stays unaffected.

try:
    UploadDataServiceProtocol  # type: ignore[name-defined]
except NameError:
    from typing import Protocol, runtime_checkable

    @runtime_checkable
    class UploadDataServiceProtocol(Protocol):
        """
        Minimal protocol for UploadDataService to satisfy imports.
        Keep permissive; implementers can define richer interfaces.
        """
        # Mark common call sites as structural — use *args/**kwargs to avoid tight coupling.
        def save_upload(self, *args, **kwargs): ...
        def get_upload(self, *args, **kwargs): ...
        def process(self, *args, **kwargs): ...
# -----------------------------------------------------------------------------
