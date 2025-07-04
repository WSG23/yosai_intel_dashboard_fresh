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
    """Serialize enhanced data to CSV string with one row per device."""
    if not data:
        return ""

    rows = []
    for fingerprint, content in data.items():
        device_mappings = (
            content.get("device_mappings")
            or content.get("mappings")
            or {}
        )

        base = {
            "fingerprint": fingerprint,
            "filename": content.get("filename"),
            "saved_at": content.get("saved_at") or content.get("learned_at"),
            "source": content.get("source"),
            "device_count": content.get("device_count")
            or content.get("file_stats", {}).get("device_count")
            or len(device_mappings),
        }

        for device_name, attrs in device_mappings.items():
            row = {**base, "device_name": device_name}
            if isinstance(attrs, dict):
                row.update(attrs)
            rows.append(row)

    df = pd.DataFrame(rows)
    return df.to_csv(index=False)


__all__ = [
    "get_enhanced_data",
    "get_device_learning_data",
    "to_json_string",
    "to_csv_string",
]
