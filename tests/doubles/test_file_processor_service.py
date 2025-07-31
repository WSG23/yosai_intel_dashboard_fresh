from __future__ import annotations

from typing import Callable, Optional, Tuple

import pandas as pd

from yosai_intel_dashboard.src.core.interfaces.protocols import FileProcessorProtocol


class FileProcessorServiceStub(FileProcessorProtocol):
    """Minimal async file processor used in tests."""

    async def process_file(
        self,
        content: str,
        filename: str,
        progress_callback: Optional[Callable[[str, int], None]] = None,
    ) -> pd.DataFrame:
        return pd.DataFrame()

    def read_uploaded_file(
        self, contents: str, filename: str
    ) -> Tuple[pd.DataFrame, str]:
        return pd.DataFrame(), ""
