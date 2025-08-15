from __future__ import annotations

from typing import Any, Callable, Dict, List

import pandas as pd

try:
    from yosai_intel_dashboard.src.core.interfaces.protocols import FileProcessorProtocol
    from yosai_intel_dashboard.src.services.upload.protocols import UploadStorageProtocol
    from yosai_intel_dashboard.src.infrastructure.callbacks import UnifiedCallbackRegistry
except Exception:  # pragma: no cover - fallback stubs for optional deps
    from typing import Any, Dict, List, Protocol

    class UploadStorageProtocol(Protocol):
        def add_file(self, filename: str, dataframe: pd.DataFrame) -> None: ...
        def get_all_data(self) -> Dict[str, pd.DataFrame]: ...
        def clear_all(self) -> None: ...
        def load_dataframe(self, filename: str) -> pd.DataFrame | None: ...
        def get_filenames(self) -> List[str]: ...
        def get_file_info(self) -> Dict[str, Dict[str, Any]]: ...
        def wait_for_pending_saves(self) -> None: ...

    class FileProcessorProtocol(Protocol):
        async def process_file(
            self,
            content: str,
            filename: str,
        ) -> pd.DataFrame: ...

        def read_uploaded_file(
            self, contents: str, filename: str
        ) -> tuple[pd.DataFrame, str]: ...

    class UnifiedCallbackRegistry:  # type: ignore[too-few-public-methods]
        def register_callback(self, *args: Any, **kwargs: Any) -> None: ...


try:
    from yosai_intel_dashboard.src.core.interfaces.service_protocols import (
        DeviceLearningServiceProtocol,
        UploadDataServiceProtocol,
    )
except Exception:  # pragma: no cover - fallback stubs
    from typing import Protocol

    class DeviceLearningServiceProtocol(Protocol):
        def get_learned_mappings(
            self, df: pd.DataFrame, filename: str
        ) -> Dict[str, Dict]: ...

        def apply_learned_mappings_to_global_store(
            self, df: pd.DataFrame, filename: str
        ) -> bool: ...

        def get_user_device_mappings(self, filename: str) -> Dict[str, Any]: ...

        def save_user_device_mappings(
            self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
        ) -> bool: ...

    class UploadDataServiceProtocol(Protocol):
        def get_uploaded_data(self) -> Dict[str, pd.DataFrame]: ...
        def get_uploaded_filenames(self) -> List[str]: ...
        def clear_uploaded_data(self) -> None: ...
        def get_file_info(self) -> Dict[str, Dict[str, Any]]: ...
        def load_dataframe(self, filename: str) -> pd.DataFrame: ...


try:
    from yosai_intel_dashboard.src.core.interfaces.protocols import ConfigurationServiceProtocol
except Exception:  # pragma: no cover - fallback stub
    from typing import Protocol

    class ConfigurationServiceProtocol(Protocol):
        ai_confidence_threshold: float
        max_upload_size_mb: int
        upload_chunk_size: int
        def get_max_upload_size_bytes(self) -> int: ...
        def validate_large_file_support(self) -> bool: ...
        def get_max_parallel_uploads(self) -> int: ...
        def get_validator_rules(self) -> Dict[str, Any]: ...
        def get_db_pool_size(self) -> int: ...


try:
    from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol
except Exception:  # pragma: no cover - fallback stub
    from typing import Protocol

    class UnicodeProcessorProtocol(Protocol):
        def clean_text(self, text: str, replacement: str = "") -> str: ...
        def safe_encode_text(self, value: Any) -> str: ...
        def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str: ...


try:
    from yosai_intel_dashboard.src.components.column_verification import (
        ColumnVerifierProtocol,
    )
except Exception:  # pragma: no cover - fallback stub to avoid heavy imports
    from typing import Protocol

    class ColumnVerifierProtocol(Protocol):
        def create_column_verification_modal(
            self, file_info: Dict[str, Any]
        ) -> Any: ...

        def register_callbacks(
            self, manager: Any, controller: Any | None = None
        ) -> None: ...


class FakeUploadStore(UploadStorageProtocol):
    def __init__(self) -> None:
        self.data: Dict[str, pd.DataFrame] = {}
        self.info: Dict[str, Dict[str, Any]] = {}

    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        self.data[filename] = dataframe
        self.info[filename] = {
            "rows": len(dataframe),
            "columns": len(dataframe.columns),
        }

    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        return self.data.copy()

    def clear_all(self) -> None:
        self.data.clear()
        self.info.clear()

    def load_dataframe(self, filename: str) -> pd.DataFrame | None:
        return self.data.get(filename)

    def get_filenames(self) -> List[str]:
        return list(self.data.keys())

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.info.copy()

    def wait_for_pending_saves(self) -> None:  # pragma: no cover - no async ops
        pass


class FakeUploadDataService(UploadDataServiceProtocol):
    def __init__(self, store: FakeUploadStore) -> None:
        self.store = store

    def get_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        return self.store.get_all_data()

    def get_uploaded_filenames(self) -> List[str]:
        return self.store.get_filenames()

    def clear_uploaded_data(self) -> None:
        self.store.clear_all()

    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        return self.store.get_file_info()

    def load_dataframe(self, filename: str) -> pd.DataFrame:
        df = self.store.load_dataframe(filename)
        if df is None:
            raise FileNotFoundError(filename)
        return df


class FakeDeviceLearningService(DeviceLearningServiceProtocol):
    def __init__(self) -> None:
        self.saved: Dict[str, Dict[str, Any]] = {}

    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict]:
        return {}

    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool:
        return False

    def get_user_device_mappings(self, filename: str) -> Dict[str, Any]:
        return self.saved.get(filename, {})

    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
    ) -> bool:
        self.saved[filename] = user_mappings
        return True

try:
    class FakeColumnVerifier(ColumnVerifierProtocol):
        def create_column_verification_modal(self, file_info: Dict[str, Any]) -> Any:
            return {"modal": file_info}

        def register_callbacks(
            self, manager: Any, controller: Any | None = None
        ) -> None:
            pass
except TypeError:  # ColumnVerifierProtocol is not a class
    class FakeColumnVerifier:  # type: ignore[too-few-public-methods]
        def create_column_verification_modal(
            self, file_info: Dict[str, Any]
        ) -> Any:
            return {"modal": file_info}

        def register_callbacks(
            self, manager: Any, controller: Any | None = None
        ) -> None:
            pass


class FakeConfigurationService(ConfigurationServiceProtocol):
    def __init__(
        self,
        max_mb: int = 50,
        chunk_size: int = 1,
        ai_threshold: float = 0.8,
    ) -> None:
        self.max_upload_size_mb = max_mb
        self.upload_chunk_size = chunk_size
        self.ai_confidence_threshold = ai_threshold

    def get_max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024

    def validate_large_file_support(self) -> bool:
        return self.max_upload_size_mb >= 50

    def get_max_parallel_uploads(self) -> int:
        return 1

    def get_validator_rules(self) -> Dict[str, Any]:
        return {}

    def get_db_pool_size(self) -> int:
        return 10


class FakeFileProcessor(FileProcessorProtocol):
    """Very small ``FileProcessorProtocol`` implementation for tests."""

    def __init__(self) -> None:
        self.callbacks = UnifiedCallbackRegistry()

    async def process_file(
        self,
        content: str,
        filename: str,
    ) -> pd.DataFrame:
        import base64
        from io import BytesIO

        _, data = content.split(",", 1)
        raw = base64.b64decode(data)
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(raw))
        else:
            df = pd.DataFrame()
        return df

    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> tuple[pd.DataFrame, str]:
        import base64
        from io import BytesIO

        _, data = contents.split(",", 1)
        raw = base64.b64decode(data)
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(BytesIO(raw))
        else:
            df = pd.DataFrame()
        return df, ""


class FakeUnicodeProcessor(UnicodeProcessorProtocol):
    def clean_text(self, text: str, replacement: str = "") -> str:
        return text.replace("\ud800", replacement).replace("\udfff", replacement)

    def safe_encode_text(self, value: Any) -> str:
        return str(value) if value is not None else ""

    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            return ""


class FakeGraphs:
    """Minimal graphs substitute used in tests."""

    GRAPH_FIGURES: dict[str, Any] = {}
