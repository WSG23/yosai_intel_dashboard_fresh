"""High-performance CSV processor using Polars"""

import logging
from typing import Dict, Any, List
from pathlib import Path
import polars as pl

from ..database.csv_storage import CSVStorageRepository
from ..services.japanese_handler import JapaneseTextHandler
from ..config import CSVProcessingConfig

logger = logging.getLogger(__name__)


class CSVProcessorService:
    """Process uploaded CSV files and store sample data."""

    def __init__(
        self,
        repository: CSVStorageRepository,
        japanese_handler: JapaneseTextHandler,
        config: CSVProcessingConfig,
    ) -> None:
        self.repository = repository
        self.japanese_handler = japanese_handler
        self.config = config
        self.logger = logger

    def process_file(
        self, file_path: str, session_id: str, client_id: str
    ) -> Dict[str, Any]:
        try:
            path = Path(file_path)
            if not path.exists():
                raise FileNotFoundError(file_path)

            df = pl.read_csv(path, encoding="utf-8")
            headers = list(df.columns)
            sample_data = df.head(self.config.sample_size).to_dicts()

            session_data = {
                "session_id": session_id,
                "client_id": client_id,
                "file_name": path.name,
                "total_rows": len(df),
                "headers": headers,
                "sample_data": sample_data,
            }

            self.repository.store_session_data(session_id, session_data)

            return {
                "success": True,
                "session_id": session_id,
                "file_info": {
                    "name": path.name,
                    "rows": len(df),
                    "columns": len(headers),
                },
                "headers": headers,
                "sample_data": sample_data,
            }

        except Exception as exc:
            self.logger.error("CSV processing failed: %s", exc)
            return {"success": False, "error": str(exc)}
