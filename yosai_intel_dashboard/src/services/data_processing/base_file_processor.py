from __future__ import annotations

import logging
from typing import IO, Callable, Iterable, List, Union

import pandas as pd

from yosai_intel_dashboard.src.infrastructure.config.constants import DEFAULT_CHUNK_SIZE
from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor as UnicodeHelper
from yosai_intel_dashboard.src.utils.file_utils import safe_decode_with_unicode_handling
from yosai_intel_dashboard.src.utils.memory_utils import check_memory_limit

logger = logging.getLogger(__name__)


class BaseFileProcessor:
    """Shared helpers for file processing operations."""

    ENCODING_PRIORITY = [
        "utf-8",
        "utf-8-sig",
        "utf-16",
        "utf-16-le",
        "utf-16-be",
        "latin1",
        "cp1252",
        "iso-8859-1",
        "ascii",
    ]

    CSV_OPTIONS = {
        "low_memory": False,
        "dtype": str,
        "keep_default_na": False,
        "na_filter": False,
        "skipinitialspace": True,
    }

    def __init__(
        self,
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        *,
        max_memory_mb: int = 500,
        decoder: Callable[[bytes, str], str] = safe_decode_with_unicode_handling,
    ) -> None:
        self.chunk_size = chunk_size
        self.max_memory_mb = max_memory_mb
        self._decoder = decoder

    def decode_with_fallback(self, content: bytes) -> str:
        """Decode ``content`` trying multiple encodings."""
        encoding = None
        try:
            import chardet as chardet_module  # type: ignore
        except ImportError:  # pragma: no cover - optional dependency
            chardet_module = None
        if chardet_module is not None:
            detected = chardet_module.detect(content)
            encoding = detected.get("encoding")
        if encoding:
            try:
                text = self._decoder(content, encoding)
                if self._is_reasonable_text(text):
                    logger.debug("Decoded content using detected %s", encoding)
                    return text
            except Exception:
                pass
        for enc in self.ENCODING_PRIORITY:
            try:
                text = self._decoder(content, enc)
                if self._is_reasonable_text(text):
                    logger.debug("Decoded content using %s", enc)
                    return text
            except Exception:
                continue
        from yosai_intel_dashboard.src.core.unicode import safe_unicode_decode

        logger.warning("All encodings failed, using replacement characters")
        return safe_unicode_decode(content, "utf-8")

    def decode_with_surrogate_handling(self, data: bytes, encoding: str) -> str:
        """Decode ``data`` and strip surrogate code points."""
        try:
            text = data.decode(encoding, errors="surrogatepass")
        except Exception:
            text = data.decode(encoding, errors="replace")
        return UnicodeHelper.clean_text(text)

    def _is_reasonable_text(self, text: str) -> bool:
        if not text.strip():
            return False
        replacement_ratio = text.count("\ufffd") / len(text)
        if replacement_ratio > 0.1:
            return False
        printable = sum(1 for c in text if c.isprintable() or c.isspace())
        return (printable / len(text)) > 0.7

    def read_large_csv(self, file_like: Union[str, IO[str]]) -> pd.DataFrame:
        """Read ``file_like`` in chunks and concatenate."""
        reader = pd.read_csv(file_like, chunksize=self.chunk_size)
        chunks: List[pd.DataFrame] = []
        for chunk in reader:
            check_memory_limit(self.max_memory_mb, logger)
            chunks.append(chunk)
        return pd.concat(chunks, ignore_index=True) if chunks else pd.DataFrame()

    def sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        return UnicodeHelper.sanitize_dataframe(df)


__all__ = ["BaseFileProcessor"]
