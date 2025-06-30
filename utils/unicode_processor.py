import logging
import re
from typing import Any

import pandas as pd


logger = logging.getLogger(__name__)


def safe_unicode_encode(value: Any) -> str:
    """Return a safe Unicode string with surrogate characters removed."""
    if value is None:
        return ""

    if isinstance(value, bytes):
        try:
            value = value.decode("utf-8", errors="surrogatepass")
        except UnicodeDecodeError:
            value = value.decode("latin-1", errors="ignore")
    else:
        value = str(value)

    try:
        # Remove any surrogate characters
        value = re.sub(r"[\uD800-\uDFFF]", "", value)
        value = value.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")
    except Exception as exc:  # pragma: no cover - unexpected
        logger.warning("Unicode encoding failed: %s", exc)
        value = value.encode("utf-8", errors="ignore").decode("utf-8", errors="ignore")

    return value


def sanitize_data_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Sanitize DataFrame column names and string cells."""
    df = df.copy()
    df.columns = [safe_unicode_encode(str(c)) for c in df.columns]

    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].apply(safe_unicode_encode)
        # Remove potential CSV injection prefixes
        df[col] = df[col].astype(str).str.replace(r"^[=+\-@]", "", regex=True)

    return df


__all__ = ["safe_unicode_encode", "sanitize_data_frame"]
