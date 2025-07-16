import re
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

try:
    from core.unicode import UnicodeProcessor
except Exception:  # pragma: no cover - fallback when core unavailable
    UnicodeProcessor = None


_SURROGATE_RE = re.compile("[\ud800-\udfff]")


def clean_text(text: str) -> str:
    """Remove surrogate characters and normalise text."""
    if text is None:
        return ""
    cleaned = _SURROGATE_RE.sub("", str(text))
    if UnicodeProcessor:
        try:
            cleaned = UnicodeProcessor.secure_unicode_sanitization(cleaned)
        except Exception:
            pass
    return cleaned


def sanitize_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize dataframe values for safe unicode handling."""
    if UnicodeProcessor:
        try:
            return UnicodeProcessor.sanitize_dataframe(df)
        except Exception:
            pass
    return df.applymap(lambda x: clean_text(x) if isinstance(x, str) else x)


def safe_file_read(path: Path, encodings: Optional[Iterable[str]] = None) -> str:
    """Read a file using multiple encodings."""
    encodings = encodings or ("utf-8-sig", "utf-8", "latin-1", "cp1252")
    for enc in encodings:
        try:
            with open(path, "r", encoding=enc, errors="replace") as fh:
                return fh.read()
        except Exception:
            continue
    raise UnicodeDecodeError("utf-8", b"", 0, 1, "Unable to decode file")


def safe_file_write(path: Path, text: str) -> None:
    """Write text to a file using UTF-8 encoding."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)
