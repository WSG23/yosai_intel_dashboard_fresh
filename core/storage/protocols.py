"""Storage domain protocols."""

from abc import abstractmethod
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class FileStorageProtocol(Protocol):
    """Protocol for file storage operations."""

    @abstractmethod
    def store_file(self, filepath: str, content: bytes) -> str:
        """Store file content and return storage ID."""
        ...

    @abstractmethod
    def retrieve_file(self, storage_id: str) -> bytes:
        """Retrieve file content by storage ID."""
        ...

    @abstractmethod
    def delete_file(self, storage_id: str) -> bool:
        """Delete file by storage ID."""
        ...


@runtime_checkable
class DatabaseStorageProtocol(Protocol):
    """Protocol for database storage operations."""

    @abstractmethod
    def store_record(self, table: str, data: Dict[str, Any]) -> str:
        """Store record in table and return record ID."""
        ...

    @abstractmethod
    def retrieve_record(self, table: str, record_id: str) -> Dict[str, Any]:
        """Retrieve record from table by ID."""
        ...

    @abstractmethod
    def update_record(
        self, table: str, record_id: str, updates: Dict[str, Any]
    ) -> bool:
        """Update record in table."""
        ...
