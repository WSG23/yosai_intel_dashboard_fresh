"""Fake unicode processor for testing."""
from __future__ import annotations

import pandas as pd
from typing import Any

from yosai_intel_dashboard.src.core.protocols import UnicodeProcessorProtocol


class FakeUnicodeProcessor(UnicodeProcessorProtocol):
    """Test implementation of UnicodeProcessor."""
    
    def clean_text(self, text: str, replacement: str = "") -> str:
        """Clean text by removing surrogates."""
        if not isinstance(text, str):
            text = str(text)
        # Remove surrogates
        text = text.replace("\ud800", replacement).replace("\udfff", replacement)
        return text.replace("\x00", "")
    
    def clean_surrogate_chars(self, text: str, replacement: str = "") -> str:
        """Remove surrogate characters."""
        if not isinstance(text, str):
            return text
        # Remove all surrogates in the range
        import re
        return re.sub(r'[\ud800-\udfff]', replacement, text)
    
    def safe_encode_text(self, value: Any) -> str:
        """Safely encode text."""
        return "" if value is None else str(value)
    
    def safe_decode_text(self, data: bytes, encoding: str = "utf-8") -> str:
        """Safely decode text."""
        return data.decode(encoding, errors="replace") if isinstance(data, bytes) else str(data)
    
    def sanitize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Sanitize dataframe."""
        cleaned = df.copy()
        # Clean column names
        cleaned.columns = [col.lstrip("=") for col in cleaned.columns]
        # Clean string values in dataframe
        for col in cleaned.columns:
            if cleaned[col].dtype == 'object':
                cleaned[col] = cleaned[col].apply(lambda x: self.clean_surrogate_chars(x) if isinstance(x, str) else x)
        return cleaned
