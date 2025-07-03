"""High level service for reading and validating uploaded files."""

import pandas as pd
import json
import logging
from typing import List, Tuple

from services import FileProcessor

logger = logging.getLogger(__name__)


class FileProcessingService:
    """Service for reading and validating uploaded files."""

    def __init__(self, processor: FileProcessor | None = None):
        self.processor = processor or FileProcessor(
            upload_folder="temp", allowed_extensions={"csv", "json", "xlsx"}
        )

    def _read_file(self, path: str) -> pd.DataFrame:
        """Read a single file into a DataFrame."""
        if path.endswith(".csv"):
            return pd.read_csv(path)
        if path.endswith(".json"):
            with open(
                path,
                "r",
                encoding="utf-8",
                errors="replace",
            ) as f:
                data = json.load(f)
            return pd.DataFrame(data)
        if path.endswith((".xlsx", ".xls")):
            return pd.read_excel(path)
        raise ValueError(f"Unsupported file type: {path}")

    def process_files(
        self, file_paths: List[str]
    ) -> Tuple[pd.DataFrame, List[str], int, int]:
        """Read and validate a list of files.

        Returns combined dataframe, log messages, number of processed files,
        and total record count.
        """
        all_data: List[pd.DataFrame] = []
        info: List[str] = []
        total_records = 0
        processed_files = 0

        for path in file_paths:
            try:
                df = self._read_file(path)
                result = self.processor._validate_data(df)
                if result.get("valid"):
                    processed_df = result.get("data", df)
                    processed_df["source_file"] = path
                    all_data.append(processed_df)
                    total_records += len(processed_df)
                    processed_files += 1
                    info.append(f"✅ {path}: {len(processed_df)} records")
                else:
                    info.append(f"❌ {path}: {result.get('error', 'Unknown error')}")
            except Exception as e:  # pragma: no cover - best effort
                info.append(f"❌ {path}: Exception - {e}")
                logger.error(f"Exception processing {path}: {e}")

        combined = (
            pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()
        )
        return combined, info, processed_files, total_records
