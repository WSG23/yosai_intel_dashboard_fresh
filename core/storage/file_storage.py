"""Simple file system storage service."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .protocols import FileStorageProtocol


class FileStorageService(FileStorageProtocol):
    """Store files on the local filesystem under a base directory."""

    def __init__(self, base_dir: str = "storage") -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def store_file(self, filepath: str, content: bytes) -> str:
        path = self.base_path / filepath
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        return str(path)

    def retrieve_file(self, storage_id: str) -> bytes:
        path = Path(storage_id)
        return path.read_bytes()

    def delete_file(self, storage_id: str) -> bool:
        path = Path(storage_id)
        if path.exists():
            path.unlink()
            return True
        return False
