"""DataFrame security validation."""

import pandas as pd
from config.dynamic_config import dynamic_config
from utils.unicode_handler import sanitize_unicode_input

from .validation_exceptions import ValidationError

class DataFrameSecurityValidator:
    """Validate DataFrames for safe processing."""

    def validate(self, df: pd.DataFrame) -> pd.DataFrame:
        max_bytes = dynamic_config.security.max_upload_mb * 1024 * 1024
        if df.memory_usage(deep=True).sum() > max_bytes:
            raise ValidationError("DataFrame too large")
        df.columns = [sanitize_unicode_input(str(c)) for c in df.columns]
        for col in df.columns:
            if df[col].astype(str).str.startswith(('=', '+', '-', '@')).any():
                raise ValidationError("Potential CSV injection detected")
        return df
