import os
from dataclasses import dataclass, field


@dataclass
class UploadConfig:
    """Settings related to file uploads."""

    folder: str = field(
        default_factory=lambda: os.getenv("UPLOAD_FOLDER", "/tmp/uploads")
    )
    max_file_size_mb: int = field(
        default_factory=lambda: int(os.getenv("MAX_FILE_SIZE_MB", "16"))
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.max_file_size_mb * 1024 * 1024


__all__ = ["UploadConfig"]
