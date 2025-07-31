from __future__ import annotations

from typing import Any, Callable, Optional, Union

import pandas as pd

from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol


class FakeUnicodeProcessor(UnicodeProcessorProtocol):
    """Minimal Unicode processor used for tests."""

    def clean_surrogate_chars(self, text: str, replacement: str = "") -> str:
        if not isinstance(text, str):
            text = str(text)
        text = text.replace("\ud800", replacement).replace("\udfff", replacement)
        return text.replace("\x00", "")

    def clean_text(self, text: str, replacement: str = "") -> str:
        """Alias for ``clean_surrogate_chars`` for protocol compliance."""
        return self.clean_surrogate_chars(text, replacement)

    def safe_decode_bytes(self, data: bytes, encoding: str = "utf-8") -> str:
        try:
            return data.decode(encoding, errors="ignore")
        except Exception:
            return ""

    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        """Alias for ``safe_decode_bytes`` for protocol compliance."""
        return self.safe_decode_bytes(data, encoding)

    def safe_encode_text(self, value: Any) -> str:
        if isinstance(value, bytes):
            return self.safe_decode_bytes(value)
        if value is None:
            return ""
        return str(value)

    def sanitize_dataframe(
        self,
        df: pd.DataFrame,
        *,
        progress: Union[bool, Callable[[int, int], None], None] = None,
    ) -> pd.DataFrame:
        df_clean = df.copy()
        df_clean.columns = [
            self.safe_encode_text(c).lstrip("=+-@") for c in df_clean.columns
        ]
        for col in df_clean.select_dtypes(include=["object"]).columns:
            df_clean[col] = df_clean[col].apply(self.safe_encode_text)
        return df_clean
