from __future__ import annotations

from typing import Any

from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol


class TestUnicodeProcessor(UnicodeProcessorProtocol):
    """Minimal Unicode processor for tests."""

    def clean_text(self, text: str, replacement: str = "") -> str:
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("\ud800", replacement).replace("\udfff", replacement)
        return text.replace("\x00", "")

    def safe_encode_text(self, value: Any) -> str:
        return "" if value is None else str(value)

    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            return ""
