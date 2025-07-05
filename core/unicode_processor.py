import logging
import unicodedata
import re
from dataclasses import dataclass, field
from typing import Any, List

import pandas as pd

logger = logging.getLogger(__name__)

# Regular expressions for unsafe characters
_SURROGATE_RE = re.compile(r"[\uD800-\uDFFF]")
_CONTROL_RE = re.compile(r"[\u0000-\u001F\u007F]")
_DANGEROUS_PREFIX_RE = re.compile(r"^[=+\-@]+")


@dataclass
class UnicodeProcessingResult:
    """Result of a Unicode processing operation."""

    text: str
    surrogates_removed: int = 0
    control_chars_removed: int = 0
    errors: List[str] = field(default_factory=list)


class UnicodeProcessor:
    """Utilities for safe Unicode handling with metrics tracking."""

    metrics = {
        "bytes_processed": 0,
        "surrogates_removed": 0,
        "control_chars_removed": 0,
    }

    @classmethod
    def _update_metrics(cls, byte_len: int, surrogates: int, controls: int) -> None:
        cls.metrics["bytes_processed"] += byte_len
        cls.metrics["surrogates_removed"] += surrogates
        cls.metrics["control_chars_removed"] += controls

    @staticmethod
    def clean_text(text: Any, *, strict: bool = False) -> UnicodeProcessingResult:
        if not isinstance(text, str):
            text = str(text) if text is not None else ""
        original_bytes = text.encode("utf-8", "surrogatepass")
        surrogates = len(_SURROGATE_RE.findall(text))
        controls = len(_CONTROL_RE.findall(text))
        cleaned = _SURROGATE_RE.sub("", text)
        cleaned = _CONTROL_RE.sub("", cleaned)
        cleaned = unicodedata.normalize("NFKC", cleaned)
        UnicodeProcessor._update_metrics(len(original_bytes), surrogates, controls)
        result = UnicodeProcessingResult(
            text=cleaned,
            surrogates_removed=surrogates,
            control_chars_removed=controls,
            errors=[],
        )
        logger.debug(
            "Cleaned text (surrogates=%s, controls=%s)", surrogates, controls
        )
        if strict and (surrogates or controls):
            result.errors.append("unsafe characters removed")
        return result

    @staticmethod
    def safe_decode(
        data: bytes,
        encoding: str = "utf-8",
        *,
        chunk_size: int = 1024 * 1024,
        strict: bool = False,
    ) -> UnicodeProcessingResult:
        pieces: List[str] = []
        errors: List[str] = []
        total_surrogates = 0
        total_controls = 0
        for start in range(0, len(data), chunk_size):
            chunk = data[start : start + chunk_size]
            try:
                text = chunk.decode(encoding, errors="surrogatepass")
            except Exception as exc:
                errors.append(str(exc))
                text = chunk.decode(encoding, errors="replace")
            res = UnicodeProcessor.clean_text(text, strict=strict)
            pieces.append(res.text)
            total_surrogates += res.surrogates_removed
            total_controls += res.control_chars_removed
            errors.extend(res.errors)
        UnicodeProcessor._update_metrics(len(data), total_surrogates, total_controls)
        return UnicodeProcessingResult(
            text="".join(pieces),
            surrogates_removed=total_surrogates,
            control_chars_removed=total_controls,
            errors=errors,
        )

    @staticmethod
    def safe_encode(
        value: Any,
        encoding: str = "utf-8",
        *,
        strict: bool = False,
    ) -> UnicodeProcessingResult:
        if isinstance(value, bytes):
            return UnicodeProcessor.safe_decode(value, encoding, strict=strict)
        res = UnicodeProcessor.clean_text(value, strict=strict)
        try:
            res.text.encode(encoding)
        except Exception as exc:
            res.errors.append(str(exc))
            if strict:
                res.text = res.text.encode(encoding, "replace").decode(encoding)
        return res

    @staticmethod
    def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        new_cols = []
        for i, col in enumerate(df.columns):
            name = UnicodeProcessor.safe_encode(col).text
            name = _DANGEROUS_PREFIX_RE.sub("", name)
            if not name:
                name = f"col_{i}"
            while name in new_cols:
                name += "_1"
            new_cols.append(name)
        df.columns = new_cols
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].apply(
                lambda x: _DANGEROUS_PREFIX_RE.sub("", UnicodeProcessor.safe_encode(x).text)
            )
        return df


__all__ = ["UnicodeProcessor", "UnicodeProcessingResult"]
