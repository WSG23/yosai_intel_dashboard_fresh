import logging
from typing import Optional, Sequence

import pandas as pd

__all__ = ["ensure_columns"]

def ensure_columns(df: pd.DataFrame, cols: Sequence[str], logger: Optional[logging.Logger] = None) -> bool:
    """Return True if all ``cols`` are present in ``df`` else log warning."""
    logger = logger or logging.getLogger(__name__)
    missing = [c for c in cols if c not in df.columns]
    if missing:
        logger.warning("Missing required columns: %s", missing)
        return False
    return True
