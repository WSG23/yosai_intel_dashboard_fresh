import base64
from typing import Iterable


class ClientSideValidator:
    """Validate uploaded file name and size before processing."""

    def __init__(self, allowed_ext: Iterable[str] | None = None, max_size: int | None = None) -> None:
        self.allowed_ext = {e.lower() for e in (allowed_ext or [".csv", ".xlsx", ".xls", ".json"])}
        self.max_size = max_size

    def validate(self, filename: str, content: str) -> tuple[bool, str]:
        ext_ok = any(filename.lower().endswith(ext) for ext in self.allowed_ext)
        if not ext_ok:
            return False, f"Unsupported file type: {filename}"
        if self.max_size is not None:
            try:
                data = content.split(',', 1)[1]
                size = len(base64.b64decode(data))
                if size > self.max_size:
                    return False, f"{filename} exceeds maximum size"
            except Exception:
                return False, "Failed to decode uploaded content"
        return True, ""

__all__ = ["ClientSideValidator"]
