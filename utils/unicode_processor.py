#!/usr/bin/env python3
"""Unicode processor with surrogate character handling."""

import pandas as pd
import logging
import re
from typing import Any, Union

logger = logging.getLogger(__name__)


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame handling Unicode surrogates that can't be encoded in UTF-8."""
    df_clean = df.copy()

    # Process string columns for Unicode issues
    for col in df_clean.select_dtypes(include=['object']).columns:
        df_clean[col] = df_clean[col].apply(clean_unicode_surrogates)

    return df_clean


def clean_unicode_surrogates(text: Any) -> str:
    """Clean Unicode surrogate characters that can't be encoded in UTF-8."""
    if pd.isna(text):
        return ""

    text_str = str(text)

    # Remove Unicode surrogates (U+D800-U+DFFF)
    text_str = re.sub(r'[\uD800-\uDFFF]', '', text_str)

    # Remove other problematic Unicode ranges
    text_str = re.sub(r'[\uFFFE\uFFFF]', '', text_str)

    # Encode to UTF-8 and decode to ensure clean text
    try:
        text_str = text_str.encode('utf-8', errors='ignore').decode('utf-8')
    except UnicodeError:
        logger.warning(f"Unicode encoding issue with text: {text_str[:50]}...")
        text_str = text_str.encode('ascii', errors='ignore').decode('ascii')

    return text_str


def sanitize_unicode_input(value: Union[str, Any]) -> str:
    """Sanitize single Unicode input value."""
    return clean_unicode_surrogates(value)

