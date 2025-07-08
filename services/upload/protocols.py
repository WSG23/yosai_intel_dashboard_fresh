"""Upload service protocol definitions."""

from abc import abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    Iterable,
    List,
    Optional,
    Protocol,
    Tuple,
    Union,
    Awaitable,
)

import pandas as pd


class UploadProcessingServiceProtocol(Protocol):
    """Protocol for upload processing operations."""

    @abstractmethod
    async def process_uploaded_files(
        self,
        contents_list: List[str],
        filenames_list: List[str],
        progress_callback: Optional[Callable[[int], None]] = None,
    ) -> Tuple[List[Any], List[Any], Dict[str, Any]]:
        """Process uploaded files and return results."""
        ...

    @abstractmethod
    def build_success_alert(self, filename: str, rows: int, cols: int) -> Any:
        """Build a success notification for an uploaded file."""
        ...

    @abstractmethod
    def build_file_preview_component(self, df: pd.DataFrame, filename: str) -> Any:
        """Return a UI component previewing the uploaded file."""
        ...


class UploadValidatorProtocol(Protocol):
    """Protocol for upload validation operations."""

    @abstractmethod
    def validate(self, filename: str, content: str) -> Tuple[bool, str]:
        """Validate uploaded file content."""
        ...

    @abstractmethod
    def to_json(self) -> str:
        """Return validator configuration as JSON."""
        ...


class FileProcessorProtocol(Protocol):
    """Protocol for processing uploaded file contents."""

    @abstractmethod
    async def process_file(
        self,
        content: str,
        filename: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> pd.DataFrame:
        """Process uploaded file content into a DataFrame."""
        ...

    @abstractmethod
    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str]:
        """Read an uploaded file and return a DataFrame and error."""
        ...


class UploadControllerProtocol(Protocol):
    """Protocol for upload controller callbacks."""

    @abstractmethod
    def upload_callbacks(self) -> List[Tuple[Any, Any, Any, Any, str, dict]]:
        """Return callback definitions for uploads."""
        ...

    @abstractmethod
    def process_uploaded_files(
        self,
        contents_list: List[str],
        filenames_list: List[str],
    ) -> Tuple[List[Any], List[Any], Dict[str, Any], Dict[str, Any]]:
        """Process files and build UI components."""
        ...


class UploadComponentProtocol(Protocol):
    """Protocol for upload UI components."""

    @abstractmethod
    def render(self) -> Any:
        """Render the component."""
        ...

    @abstractmethod
    def safe_unicode_encode(self, text: Union[str, bytes, None]) -> str:
        """Safely encode arbitrary text."""
        ...

    @abstractmethod
    def decode_upload_content(self, content: str, filename: str) -> Tuple[bytes, str]:
        """Decode upload contents with error handling."""
        ...


class UploadStorageProtocol(Protocol):
    """Protocol for storing uploaded data."""

    @abstractmethod
    def add_file(self, filename: str, dataframe: pd.DataFrame) -> None:
        """Persist uploaded file data."""
        ...

    @abstractmethod
    def get_all_data(self) -> Dict[str, pd.DataFrame]:
        """Return all stored dataframes."""
        ...

    @abstractmethod
    def clear_all(self) -> None:
        """Remove all stored upload data."""
        ...

    @abstractmethod
    def load_dataframe(self, filename: str) -> pd.DataFrame | None:
        """Load a previously stored dataframe."""
        ...

    @abstractmethod
    def get_filenames(self) -> List[str]:
        """Return list of stored filenames."""
        ...

    @abstractmethod
    def get_file_info(self) -> Dict[str, Dict[str, Any]]:
        """Return info dictionary for stored files."""
        ...

    @abstractmethod
    def wait_for_pending_saves(self) -> None:
        """Block until any background saves are complete."""

        ...


class UploadAnalyticsProtocol(Protocol):
    """Protocol for analyzing uploaded data."""

    @abstractmethod
    def analyze_uploaded_data(self) -> Dict[str, Any]:
        """Analyze uploaded data and return metrics."""
        ...

    @abstractmethod
    def load_uploaded_data(self) -> Dict[str, pd.DataFrame]:
        """Load uploaded data for analysis."""
        ...


class UploadSecurityProtocol(Protocol):
    """Protocol for security validation of uploads."""

    @abstractmethod
    def validate_file_upload(self, filename: str, content: bytes) -> Dict[str, Any]:
        """Validate uploaded file for security issues."""
        ...

    @abstractmethod
    def sanitize_dataframe_unicode(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize a DataFrame for unsafe Unicode."""
        ...


class DeviceLearningServiceProtocol(Protocol):
    """Protocol for persistent device mapping learning."""

    @abstractmethod
    def get_learned_mappings(self, df: pd.DataFrame, filename: str) -> Dict[str, Dict]:
        """Retrieve previously learned mappings for ``filename``."""
        ...

    @abstractmethod
    def apply_learned_mappings_to_global_store(
        self, df: pd.DataFrame, filename: str
    ) -> bool:
        """Apply learned mappings to the global AI mapping store."""
        ...

    @abstractmethod
    def save_user_device_mappings(
        self, df: pd.DataFrame, filename: str, user_mappings: Dict[str, Any]
    ) -> bool:
        """Persist user-confirmed device mappings."""
        ...


class UploadQueueManagerProtocol(Protocol):
    """Protocol for managing queued uploads."""

    files: List[Any]

    @abstractmethod
    def add_files(self, files: Iterable[Any], *, priority: int = 0) -> None: ...

    @abstractmethod
    def add_file(self, file: Any, *, priority: int = 0) -> None: ...

    @abstractmethod
    def mark_complete(self, file: Any) -> None: ...

    @abstractmethod
    def overall_progress(self) -> int: ...

    @abstractmethod
    def get_queue_status(self) -> Dict[str, Any]: ...

    @abstractmethod
    async def process_queue(
        self,
        handler: Callable[[Any], Awaitable[Any]],
        *,
        max_concurrent: int | None = None,
    ) -> List[Tuple[str, Any]]: ...


from core.enhanced_container import ServiceContainer


def _get_container(
    container: ServiceContainer | None = None,
) -> ServiceContainer | None:
    if container is not None:
        return container
    try:  # pragma: no cover - dash may be missing in tests
        from dash import get_app

        app = get_app()
        return getattr(app, "_service_container", None)
    except Exception:
        return None


def get_device_learning_service(
    container: ServiceContainer | None = None,
) -> DeviceLearningServiceProtocol:
    c = _get_container(container)
    if c and c.has("device_learning_service"):
        return c.get("device_learning_service")
    from services.device_learning_service import get_device_learning_service as _get

    return _get()
