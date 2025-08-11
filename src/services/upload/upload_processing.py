from __future__ import annotations

import hashlib
import mimetypes
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from unicode_toolkit import safe_encode_text


@dataclass
class UploadResult:
    """Metadata returned after successfully streaming an upload."""

    filename: str
    bytes: int
    sha256: str
    content_type: str

    @property
    def contentType(self) -> str:  # pragma: no cover - alias for camelCase access
        return self.content_type


def stream_upload(
    source: BinaryIO,
    destination: str | Path,
    filename: str,
    *,
    max_bytes: int = 10 * 1024 * 1024,
    allowed_extensions: set[str] | None = None,
    chunk_size: int = 1024 * 1024,
) -> UploadResult:
    """Stream ``source`` to ``destination`` enforcing limits and return metadata.

    The function writes the uploaded content to a temporary file while
    calculating its SHA-256 hash. Once streaming finishes successfully the
    temporary file is atomically moved to the final destination.
    """

    allowed = allowed_extensions or {".csv", ".json", ".xlsx"}

    dest_dir = Path(destination)
    dest_dir.mkdir(parents=True, exist_ok=True)

    safe_name = safe_encode_text(Path(filename).name).replace(" ", "_")
    ext = Path(safe_name).suffix.lower()
    if ext not in allowed:
        raise ValueError(f"Unsupported file extension: {ext}")

    hasher = hashlib.sha256()
    total = 0

    with tempfile.NamedTemporaryFile(dir=dest_dir, delete=False) as tmp:
        tmp_path = Path(tmp.name)
        while True:
            chunk = source.read(chunk_size)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                tmp.close()
                try:
                    tmp_path.unlink()
                finally:
                    pass
                raise ValueError("file too large")
            hasher.update(chunk)
            tmp.write(chunk)

    final_path = dest_dir / safe_name
    os.replace(tmp_path, final_path)

    content_type = mimetypes.guess_type(safe_name)[0] or "application/octet-stream"

    return UploadResult(
        filename=safe_name,
        bytes=total,
        sha256=hasher.hexdigest(),
        content_type=content_type,
    )
