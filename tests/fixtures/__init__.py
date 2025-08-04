from __future__ import annotations

import sys
from contextlib import contextmanager
from pathlib import Path
from types import ModuleType


@contextmanager
def setup_test_environment():
    """Register common stubs used in integration tests.

    This sets up lightweight stand-ins for components that would otherwise
    require heavy imports.  The original modules are restored once the
    context exits.
    """
    original: dict[str, ModuleType | None] = {}

    def register(name: str, module: ModuleType) -> None:
        original[name] = sys.modules.get(name)
        sys.modules[name] = module

    # -- Security validator -------------------------------------------------
    validation_pkg = ModuleType("validation")
    validation_pkg.__path__ = []
    register("validation", validation_pkg)

    sec_mod = ModuleType("validation.security_validator")

    class SecurityValidator:  # type: ignore[too-few-public-methods]
        def validate_input(self, value, name: str = ""):
            return {"sanitized": value}

        def validate_file_meta(self, filename: str, content: bytes):
            return {
                "valid": True,
                "filename": Path(filename).name,
                "issues": [],
            }

        def sanitize_filename(self, filename: str) -> str:
            return Path(filename).name

        def validate_resource_access(self, *args, **kwargs):
            return True

        def validate_file_upload(
            self, content: bytes
        ):  # pragma: no cover - simple stub
            return type("Result", (), {"valid": True, "message": ""})()

    sec_mod.SecurityValidator = SecurityValidator
    register("validation.security_validator", sec_mod)

    # -- Upload processing service -----------------------------------------
    proc_mod = ModuleType("yosai_intel_dashboard.src.services.upload.processor")

    class UploadProcessingService:  # type: ignore[too-few-public-methods]
        async_processor = None

        def __init__(self, *args, **kwargs) -> None:
            pass

        async def process_files(
            self, *args, **kwargs
        ):  # pragma: no cover - simple stub
            return ([], [], {}, [], {}, None, None)

    proc_mod.UploadProcessingService = UploadProcessingService
    register(
        "yosai_intel_dashboard.src.services.upload.processor",
        proc_mod,
    )

    # -- Callback manager ---------------------------------------------------
    analytics_pkg = ModuleType("analytics_core")
    analytics_pkg.__path__ = []
    register("analytics_core", analytics_pkg)

    callbacks_pkg = ModuleType("analytics_core.callbacks")
    callbacks_pkg.__path__ = []
    register("analytics_core.callbacks", callbacks_pkg)

    cb_mod = ModuleType("analytics_core.callbacks.unified_callback_manager")

    class CallbackManager:  # type: ignore[too-few-public-methods]
        def trigger(self, *args, **kwargs):
            pass

        async def trigger_async(self, *args, **kwargs):
            return []

    cb_mod.CallbackManager = CallbackManager
    register("analytics_core.callbacks.unified_callback_manager", cb_mod)

    # -- Upload data store --------------------------------------------------
    utils_pkg = ModuleType("yosai_intel_dashboard.src.utils")
    utils_pkg.__path__ = []
    register("yosai_intel_dashboard.src.utils", utils_pkg)

    store_mod = ModuleType("yosai_intel_dashboard.src.utils.upload_store")

    class UploadedDataStore:  # type: ignore[too-few-public-methods]
        def __init__(self) -> None:
            self._data: dict[str, object] = {}

        def add_file(self, filename, dataframe):
            self._data[filename] = dataframe

        def get_all_data(self):
            return self._data.copy()

        def clear_all(self) -> None:
            self._data.clear()

        def load_dataframe(self, filename):
            return self._data.get(filename)

        def get_filenames(self):
            return list(self._data.keys())

        def get_file_info(self):  # pragma: no cover - simple stub
            return {name: {} for name in self._data}

        def wait_for_pending_saves(self):  # pragma: no cover - no async ops
            pass

    _uploaded_store = UploadedDataStore()
    store_mod.UploadedDataStore = UploadedDataStore
    store_mod.get_uploaded_data_store = lambda: _uploaded_store
    store_mod.uploaded_data_store = _uploaded_store
    register(
        "yosai_intel_dashboard.src.utils.upload_store",
        store_mod,
    )

    try:
        yield
    finally:
        for name, module in original.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def create_test_analytics_service():
    """Return a lightweight analytics service stub."""
    from tests.stubs.services.analytics_service import AnalyticsService

    return AnalyticsService()


def create_test_container():
    """Return a minimal service container for tests."""

    class _Container:  # type: ignore[too-few-public-methods]
        def __init__(self) -> None:
            self._services: dict[str, object] = {}

        def register_singleton(self, name: str, instance: object) -> "_Container":
            self._services[name] = instance
            return self

        def get(self, name: str) -> object | None:
            return self._services.get(name)

    return _Container()
