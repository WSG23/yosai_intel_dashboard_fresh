from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path


class FileValidator:
    """Basic upload security checks."""

    ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json", ".txt"}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    EXTENSION_MIME_MAP = {
        ".csv": "text/csv",
        ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        ".json": "application/json",
        ".txt": "text/plain",
    }

    MALICIOUS_PATTERNS = [
        re.compile(rb"\x00"),
        re.compile(rb"<script", re.IGNORECASE),
    ]

    def __init__(self, storage_dir: str | Path) -> None:
        self.storage_dir = Path(storage_dir).resolve()

    def validate(self, filename: str, mime: str, data: bytes) -> None:
        """Raise ``ValueError`` if the file fails any checks."""

        if "\x00" in filename:
            raise ValueError("Null byte in filename")

        name = Path(filename).name
        parts = name.lower().split(".")
        if len(parts) > 2:
            prior_exts = {f".{p}" for p in parts[1:-1]}
            if any(p not in self.ALLOWED_EXTENSIONS for p in prior_exts):
                raise ValueError("Double extension detected")
        ext = f".{parts[-1]}" if len(parts) > 1 else ""
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError("Unsupported file extension")

        expected_mime = self.EXTENSION_MIME_MAP.get(ext)
        if expected_mime and mime != expected_mime:
            raise ValueError("MIME type mismatch")

        dest = (self.storage_dir / filename).resolve()
        if not dest.is_relative_to(self.storage_dir):
            raise ValueError("Path traversal detected")

        if len(data) > self.MAX_FILE_SIZE:
            raise ValueError("File too large")

        for pattern in self.MALICIOUS_PATTERNS:
            if pattern.search(data):
                raise ValueError("Malicious content detected")

        # Simple zip bomb detection
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                total_uncompressed = sum(i.file_size for i in zf.infolist())
                compressed = sum(i.compress_size for i in zf.infolist())
                if total_uncompressed > self.MAX_FILE_SIZE or (
                    compressed and total_uncompressed / compressed > 10
                ):
                    raise ValueError("Zip bomb detected")
        except zipfile.BadZipFile:
            # Not a zip file
            pass
