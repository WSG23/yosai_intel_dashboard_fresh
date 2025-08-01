from __future__ import annotations

"""High level interface aggregating Unicode helpers."""

import logging
from pathlib import Path
from typing import Any, Callable

from yosai_intel_dashboard.src.core.container import get_unicode_processor
from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol

from .unicode_processor import (
    FileUnicodeHandler,
    QueryUnicodeHandler,
    UnicodeSecurityValidator,
)

logger = logging.getLogger(__name__)


class UnicodeHandler:
    """Convenience wrapper combining common Unicode operations."""

    def __init__(self, processor: UnicodeProcessorProtocol | None = None) -> None:
        self.processor = processor or get_unicode_processor()

    # ------------------------------------------------------------------
    # Text helpers
    def clean_text(self, text: Any) -> str:
        return self.processor.safe_encode_text(text)

    def decode_bytes(self, data: bytes, encoding: str = "utf-8") -> str:
        return self.processor.safe_decode_text(data, encoding)

    def process_dict(self, data: Any) -> Any:
        return self.processor.process_dict(data)

    # ------------------------------------------------------------------
    # Query helpers
    def encode_query(
        self,
        query: str,
        *,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> str:
        return QueryUnicodeHandler.handle_unicode_query(
            query,
            processor=self.processor,
            on_surrogate=on_surrogate,
        )

    def encode_params(
        self,
        params: Any,
        *,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> Any:
        return QueryUnicodeHandler.handle_query_parameters(
            params,
            processor=self.processor,
            on_surrogate=on_surrogate,
        )

    # ------------------------------------------------------------------
    # File helpers
    def clean_file_content(
        self,
        content: str | bytes,
        *,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> str:
        return FileUnicodeHandler.handle_file_content(
            content,
            processor=self.processor,
            on_surrogate=on_surrogate,
        )

    def clean_filename(
        self,
        name: str | Path,
        *,
        on_surrogate: Callable[[str], None] | None = None,
    ) -> str:
        return FileUnicodeHandler.handle_filename(
            name,
            processor=self.processor,
            on_surrogate=on_surrogate,
        )

    # ------------------------------------------------------------------
    # Security helpers
    def sanitize_input(self, text: Any) -> str:
        return UnicodeSecurityValidator.validate_input(text)

    def check_for_attacks(self, text: Any) -> bool:
        return UnicodeSecurityValidator.check_for_attacks(text)


__all__ = ["UnicodeHandler"]
