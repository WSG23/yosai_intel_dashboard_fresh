import logging
from typing import Dict, Any, List
import pandas as pd
from utils.upload_store import uploaded_data_store

logger = logging.getLogger(__name__)


def get_uploaded_data() -> Dict[str, pd.DataFrame]:
    """Return all uploaded data from the persistent store."""
    return uploaded_data_store.get_all_data()


def get_uploaded_filenames() -> List[str]:
    """Return names of uploaded files."""
    return uploaded_data_store.get_filenames()


def clear_uploaded_data() -> None:
    """Remove all uploaded data."""
    uploaded_data_store.clear_all()
    logger.info("Uploaded data cleared")


def get_file_info() -> Dict[str, Dict[str, Any]]:
    """Return metadata for uploaded files."""
    return uploaded_data_store.get_file_info()


def load_dataframe(filename: str) -> pd.DataFrame:
    """Load a single uploaded file on demand."""
    return uploaded_data_store.load_dataframe(filename)

__all__ = [
    "get_uploaded_data",
    "get_uploaded_filenames",
    "clear_uploaded_data",
    "get_file_info",
    "load_dataframe",
]
