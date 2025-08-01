from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

from yosai_intel_dashboard.src.core.container import get_unicode_processor
from yosai_intel_dashboard.src.core.interfaces.protocols import UnicodeProcessorProtocol


class BaseReader:
    """Base class for file readers."""

    format_name: str = "base"

    class CannotParse(Exception):
        """Raised when a reader cannot parse a file."""

    def __init__(
        self, *, unicode_processor: UnicodeProcessorProtocol | None = None
    ) -> None:
        self.unicode_processor = unicode_processor or get_unicode_processor()

    def read(self, file_path: str, hint: Optional[Dict] = None) -> pd.DataFrame:
        raise NotImplementedError

    def _sanitize(self, df: pd.DataFrame) -> pd.DataFrame:
        return self.unicode_processor.sanitize_dataframe(df)
