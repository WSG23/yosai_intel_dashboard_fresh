from __future__ import annotations

from pathlib import Path
from typing import Any


class MockSecurityValidator:
    """Simple validator used across tests."""

    def validate_file_meta(self, filename: str, content: Any) -> dict[str, Any]:
        return {"valid": True, "filename": Path(filename).name, "issues": []}

    def sanitize_filename(self, filename: str) -> str:
        return Path(filename).name

    def validate_file_upload(self, filename: str, content: Any) -> dict[str, Any]:
        if filename.endswith(".exe"):
            raise ValueError("unsupported")
        if hasattr(content, "__len__") and len(content) > 5:
            raise ValueError("too_large")
        return {"valid": True, "message": ""}


class MockProcessor:
    """Minimal processor with optional validator and database access."""

    def __init__(self, df: Any | None = None) -> None:
        self.df = df
        self.validator = MockSecurityValidator()
        self.calls: list[tuple[Any, str]] = []

    def get_processed_database(self):
        return self.df, {}

    def process_file_async(self, contents: Any, filename: str) -> str:
        self.calls.append((contents, filename))
        return "job123"

    def get_job_status(self, job_id: str) -> dict[str, Any]:
        return {}


class MockCallbackManager:
    """Capture triggered callback events for assertions."""

    def __init__(self) -> None:
        self.events: list[tuple[Any, str, dict[str, Any]]] = []

    def trigger(self, event: Any, source: str, payload: dict[str, Any]) -> None:
        self.events.append((event, source, payload))


class MockUploadDataStore:
    """In-memory storage used for upload tests."""

    def __init__(self, storage_dir: Any | None = None) -> None:
        self.storage_dir = storage_dir
        self.files: dict[str, Any] = {}

    def add_file(self, name: str, df: Any) -> None:
        self.files[name] = df

