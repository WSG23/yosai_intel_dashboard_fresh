import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def investigate_data() -> dict:
    """Read file information from UPLOAD_FOLDER/file_info.json."""
    folder = Path(os.environ.get("UPLOAD_FOLDER", "."))
    info_file = folder / "file_info.json"
    if not info_file.exists():
        logger.info("file_info.json not found: %s", info_file)
        return {}
    with open(info_file, encoding="utf-8") as fh:
        return json.load(fh)


__all__ = ["investigate_data"]
