"""Export helpers for enhanced learning data."""

import json
from typing import Dict, Any
import pandas as pd

from services.consolidated_learning_service import get_learning_service
from services.device_learning_service import get_device_learning_service


def get_enhanced_data() -> Dict[str, Any]:
    """Return enhanced mapping data from the learning service."""
    service = get_learning_service()
    return service.learned_data


def get_device_learning_data() -> Dict[str, Any]:
    """Return raw device learning mappings."""
    service = get_device_learning_service()
    return service.learned_mappings


def to_json_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to pretty JSON string."""
    return json.dumps(data, indent=2, ensure_ascii=False)


def to_csv_string(data: Dict[str, Any]) -> str:
    """Serialize enhanced data to CSV string with JSON encoded mappings."""
    if not data:
        return ""

    records = []
    for fingerprint, content in data.items():
        stats = content.get("file_stats", {})
        record = {
            "fingerprint": fingerprint,
            "filename": content.get("filename", ""),
            "saved_at": content.get("saved_at", ""),
            "device_mappings": json.dumps(content.get("device_mappings", {})),
            "column_mappings": json.dumps(content.get("column_mappings", {})),
            "row_count": stats.get("rows", 0),
            "column_count": len(stats.get("columns", [])),
            "device_count": stats.get("device_count", 0),
        }
        records.append(record)

    df = pd.DataFrame.from_records(records)
    return df.to_csv(index=False)


__all__ = [
    "get_enhanced_data",
    "get_device_learning_data",
    "to_json_string",
    "to_csv_string",
]
