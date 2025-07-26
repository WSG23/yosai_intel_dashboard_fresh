from __future__ import annotations

import logging



from config.constants import DEFAULT_CHUNK_SIZE

from services.data_processing.base_file_processor import BaseFileProcessor


logger = logging.getLogger(__name__)


class FileProcessor(BaseFileProcessor):
    """Process CSV files in chunks while guarding memory usage."""

    def __init__(self, chunk_size: int = DEFAULT_CHUNK_SIZE, *, max_memory_mb: int = 500) -> None:
        super().__init__(chunk_size=chunk_size, max_memory_mb=max_memory_mb)


__all__ = ["FileProcessor"]
