#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
from typing import Union

from yosai_intel_dashboard.src.core.unicode import UnicodeProcessor

_processor = UnicodeProcessor()


def safe_decode(data: bytes, encoding: str = "utf-8") -> str:
    """Decode bytes using ``encoding`` and sanitize the result."""
    try:
        text = data.decode(encoding, errors="surrogatepass")
    except Exception:
        text = data.decode(encoding, errors="ignore")
    return _processor.process(text)


try:  # Optional dependency
    import chardet
except Exception:  # pragma: no cover - optional
    chardet = None


class RobustFileReader:
    ENCODING_PRIORITY = ["utf-8", "latin-1", "cp1252", "iso-8859-1"]

    @staticmethod
    def read_text_with_detection(file_path: Union[str, Path]) -> str:
        path = Path(file_path)
        raw_bytes = path.read_bytes()

        if chardet:
            detected = chardet.detect(raw_bytes)
            if detected.get("encoding"):
                try:
                    return safe_decode(raw_bytes, detected["encoding"])
                except Exception:
                    pass

        for encoding in RobustFileReader.ENCODING_PRIORITY:
            try:
                return safe_decode(raw_bytes, encoding)
            except Exception:
                continue
        return safe_decode(raw_bytes, "utf-8")


def safe_read_text(file_path: Union[str, Path]) -> str:
    return RobustFileReader.read_text_with_detection(file_path)
